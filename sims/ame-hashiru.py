"""雨の中、走ると濡れない？ 傘なしで100m、1万人が思い思いの速さで。— 2026-10-07 作成（公開予定 10/9）

モデル（横から見た2次元＋奥行きは幅で扱う。雨は鉛直に一定の速さで落ち、空間にでたらめ＝一様（ポアソン）に分布）
  雨      : 1時間に10mm（気象庁の「やや強い雨」＝10〜20mm/h の下の端）。雨粒は直径2mmの球で、落ちる速さ 6.49 m/s
            （Gunn & Kinzer 1949 の、静止した空気での終端速度。2mm のとき 6.49 m/s）。
            1粒の体積 4.19 mm³ → 空間の雨粒の数密度 n = (10mm/h) ÷ (6.49 m/s × 4.19 mm³) ≈ 102個/m³。
            ※本物の雨は粒の大きさがばらつく。ここでは全部同じ大きさ（2mm）にそろえた。
  人      : 直方体。幅（横）0.45m × 奥行き（進む向き）0.25m × 高さ1.7m。
            上から見た面積（頭と肩）= 0.45×0.25 = 0.1125 m²、前から見た面積（体の正面）= 0.45×1.7 = 0.765 m²。
            全員同じ体つき（1万人の違いは速さと、雨粒がどこに落ちるかの偶然だけ）。
  動き    : 100m を一定の速さ v で進む（時間 T = 100/v）。追い風のとき、雨粒は水平に w=3 m/s で流れる（落ちる速さは同じ）。
  数え方  : 雨粒を実際に空間へまき（ポアソン分布）、動く直方体にいつ・どの面から入るかを1粒ずつ調べて、
            0〜T 秒のあいだに体に入った粒を数える（はじめから体の中にあった粒は数えない）。1粒は1回だけ。
  答えの照合に使う式（理論値）:
            当たる粒の期待値 = n × 幅 × T × ( 奥行き×落ちる速さ + 高さ×|w − v| )
            = 上から（降る量×上面積×時間。時間に比例）＋ 前から（空間の雨の密度×前面積×距離。速さに関係しない）
            無風なら 前から の項は n×前面積×100m ＝ 約7,800粒（これが「底」）。

問い: 「傘なしで100m。走ると、歩くより濡れない？」 A 半分以下 ／ B 少し減る ／ C 変わらない。答えは B（歩き1.4m/s → 走り5m/s で約3割減）。
見せ方: 冒頭＝雨の道を歩く人と走る人。答え合わせ1＝2人に当たった雨粒が色の点（青＝上から、橙＝前から）で体に残る。
        答え合わせ2＝1万人（1〜7 m/s）の散布図。驚き＝上から／前から の棒。ひねり＝追い風（風と同じ速さで谷ができる）。
        締め＝「なんで全力で走っても、半分にもならないの？ → 答えは概要欄に」。

照合（check_answers）:
 (1) 力ずくの数え方（広い箱に雨粒をまいて全部調べる）の平均が、理論値と一致（歩き・走り・全力・追い風）
 (2) 速い数え方（当たる範囲だけにまく）の1万人の平均のずれ・ばらつきが、理論値とポアソンの分散に一致（無風・追い風）
 (3) 無風の1万人は全員が「底」（前から当たる分）より上
 (4) 追い風の谷が風の速さ（3 m/s）にできて、谷の高さが理論値と一致
 (5) 画面に出す数字（歩き・走りの粒数、減った割合）が理論値と同じ丸め
 (6) 答えは B（走っても半分以下にはならず、3割前後は減る）
乱数の種は、冒頭〜答え合わせ1の見本（歩く人・走る人）を「ふつうの結果」にするために選んでよい。画面の統計は1万人すべてから正直に出している。
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
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, _t, SR)
from engine.parts import loop_back, stills

note.use()
note.DATE = "10.9"                                # 日付欄（公開予定日）

SLUG = "ame-hashiru"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
D = 100.0                                         # 道のり（m）
U = 6.49                                          # 雨粒の落ちる速さ（m/s）Gunn & Kinzer 1949: 直径2mm
DIA = 2.0e-3                                      # 雨粒の直径（m）
RAIN_MMH = 10.0                                   # 雨の強さ（mm/h）
DROP_VOL = math.pi / 6 * DIA ** 3                 # 1粒の体積（m³）
NDENS = (RAIN_MMH / 1000 / 3600) / (U * DROP_VOL)  # 空間の雨粒の数密度（個/m³）
BW, BL, BH = 0.45, 0.25, 1.70                     # 人: 幅・奥行き（進む向き）・高さ（m）
A_TOP, A_FRONT = BW * BL, BW * BH
WIND = 3.0                                        # 追い風（雨粒が水平に流れる速さ m/s。進む向きと同じ）
V_WALK, V_RUN = 1.4, 5.0                          # 冒頭の2人（m/s）。時速5km・時速18km
V_LO, V_HI = 1.0, 7.0                             # 1万人の速さの範囲（m/s）
N_PEOPLE = 10000


def expected(v, w=0.0):
    """当たる粒の期待値（理論値）"""
    v = np.asarray(v, dtype=float)
    return NDENS * BW * (D / v) * (BL * U + BH * np.abs(w - v))


def floor_hits():
    """底: 前から当たる分（無風。速さに関係しない）"""
    return NDENS * A_FRONT * D


# ---------- 1人ぶん: 雨粒をまいて、体に入る粒を数える ----------

def _drops(v, w, rng, dx=0.2):
    """この人に当たりうる範囲に雨粒をまく。まく範囲は、当たりうる粒がすべて入る大きさ（広めの範囲）。
    その中のどの粒が当たるかは、あとで1粒ずつ調べる"""
    c = w - v
    if abs(c) < 1e-6:
        c = 1e-6
    T = D / v
    xa = -BL - max(0.0, c * T)
    xb = -min(0.0, c * T)
    nb = int(math.ceil((xb - xa) / dx))
    e0 = xa + dx * np.arange(nb)
    e1 = np.minimum(e0 + dx, xb)

    def tx(x):
        ta, tb = (-BL - x) / c, (-x) / c
        return np.minimum(ta, tb), np.maximum(ta, tb)
    i0, o0 = tx(e0)
    i1, o1 = tx(e1)
    t_lo = np.maximum(0.0, np.minimum(i0, i1))
    t_hi = np.minimum(T, np.maximum(o0, o1))
    ok = t_hi > t_lo
    zlo = U * t_lo
    zhi = U * t_hi + BH
    lam = np.where(ok, NDENS * BW * (e1 - e0) * (zhi - zlo), 0.0)
    cnt = rng.poisson(lam)
    idx = np.repeat(np.arange(nb), cnt)
    x0 = e0[idx] + rng.random(len(idx)) * (e1 - e0)[idx]
    z0 = zlo[idx] + rng.random(len(idx)) * (zhi - zlo)[idx]
    return x0, z0, c, T


def _drops_loose(v, w, rng):
    """力ずくの照合用: 広い箱（x は当たりうる範囲、高さは 0〜BH+U×T）にまるごとまく。当たらない粒がほとんど"""
    c = w - v
    T = D / v
    xa = -BL - max(0.0, c * T)
    xb = -min(0.0, c * T)
    zt = BH + U * T
    n = rng.poisson(NDENS * BW * (xb - xa) * zt)
    return xa + rng.random(n) * (xb - xa), rng.random(n) * zt, c, T


def _test(x0, z0, c, T):
    """1粒ずつ、動く直方体に入るかを調べる。返り値: 当たったか、入った時刻、上から入ったか"""
    ta, tb = (-BL - x0) / c, (-x0) / c
    txi, txo = np.minimum(ta, tb), np.maximum(ta, tb)
    tzi, tzo = (z0 - BH) / U, z0 / U
    ti, to = np.maximum(txi, tzi), np.minimum(txo, tzo)
    hit = (ti < to) & (ti > 0) & (ti <= T)
    return hit, ti, tzi > txi


def person(v, w, seed, loose=False, record=False):
    rng = np.random.default_rng(seed)
    x0, z0, c, T = (_drops_loose if loose else _drops)(v, w, rng)
    hit, ti, top = _test(x0, z0, c, T)
    if not record:
        return int(hit.sum())
    h = hit
    t_in = ti[h]
    is_top = top[h]
    xi = x0[h] + c * t_in                          # 入った瞬間の、体の前端から見た位置（-BL〜0）
    zz = z0[h] - U * t_in                          # 入った瞬間の高さ（0〜BH）
    o = np.argsort(t_in)
    return dict(t=t_in[o], top=is_top[o], xi=xi[o], z=zz[o], front=(c < 0), n=int(h.sum()))


def _chunk(args):
    vs, w, seed = args
    out = np.empty(len(vs), np.int64)
    for k, v in enumerate(vs):
        out[k] = person(float(v), w, seed * 100003 + k)
    return out


def many(vs, w, seed, chunk=250):
    """vs の1人ずつを別々の乱数で。別プロセスに分けて回す"""
    jobs = [(vs[i:i + chunk], w, seed * 1000 + i // chunk) for i in range(0, len(vs), chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        return np.concatenate(list(ex.map(_chunk, jobs)))


# ---------- 画面に出すデータ（1万人×2、見本の2人、力ずくの照合） ----------
SEED_P, SEED_W = 1, 2                             # 1万人（無風・追い風）の種


def _loose_check():
    """力ずくの照合: 広い箱にまいて全部調べた平均 vs 理論値（人数は少なめ）"""
    res = []
    for v, w, n in ((V_WALK, 0.0, 12), (3.0, 0.0, 30), (V_RUN, 0.0, 40), (7.0, 0.0, 40), (1.5, WIND, 6), (V_RUN, WIND, 40), (3.0 + 0.5, WIND, 40)):
        hs = np.array([person(v, w, 70000 + 17 * k + int(v * 10), loose=True) for k in range(n)], float)
        res.append((v, w, n, float(hs.mean()), float(expected(v, w)), float(hs.std(ddof=1) / math.sqrt(n))))
    return res


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED_P)
    vp = V_LO + (V_HI - V_LO) * rng.random(N_PEOPLE)
    rng2 = np.random.default_rng(SEED_W)
    vw = V_LO + (V_HI - V_LO) * rng2.random(N_PEOPLE)
    hp = many(vp, 0.0, SEED_P)
    hw = many(vw, WIND, SEED_W)
    # 別の乱数で1万人やり直す（画面の数字が同じ丸めか）
    rng3 = np.random.default_rng(99)
    vq = V_LO + (V_HI - V_LO) * rng3.random(N_PEOPLE)
    hq = many(vq, 0.0, 99)
    loose = _loose_check()
    np.savez(OUT / "data.npz", vp=vp, hp=hp, vw=vw, hw=hw, vq=vq, hq=hq, loose=np.array(loose))


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = OUT / "data.npz"
        if not f.exists():
            compute()
        z = np.load(f)
        _DATA = {k: z[k] for k in z.files}
    return _DATA


def binned_mean(v, h, lo, hi):
    m = (v >= lo) & (v < hi)
    return float(h[m].mean()), int(m.sum())


if __name__ == "__main__" and "--compute" in sys.argv:
    import time
    t0 = time.time()
    d = data()
    print(f"計算 {time.time() - t0:.0f}秒")
    print("数密度 n =", NDENS, " 底 =", floor_hits(), " A_top =", A_TOP, " A_front =", A_FRONT)
    for v in (1, 1.4, 2, 3, 5, 7):
        print(f"v={v}: 無風 {float(expected(v)):.0f}  追い風 {float(expected(v, WIND)):.0f}")
    for r in d["loose"]:
        print("力ずく v=%.1f w=%.1f n=%d 平均 %.0f 理論 %.0f 標準誤差 %.0f" % tuple(r))


# ---------- 見本の2人（冒頭〜答え合わせ1）の記録 ----------
def find_seed(v, n_try=400):
    """見本の人を「ふつうの結果」にする種を探す（期待値からの差が標準偏差の0.2倍以内で、いちばん近いもの）"""
    e = float(expected(v))
    best = None
    for s in range(1, n_try):
        n = person(v, 0.0, 5000 + s)
        z = abs(n - e) / math.sqrt(e)
        if best is None or z < best[0]:
            best = (z, s)
    return best[1]


WALK_SEED, RUN_SEED = 383, 156                    # 探索（--seeds）で選んだ見本の種（期待値にいちばん近い結果）


_REC = {}


def rec(kind):
    if kind not in _REC:
        v, s = (V_WALK, WALK_SEED) if kind == "walk" else (V_RUN, RUN_SEED)
        _REC[kind] = person(v, 0.0, 5000 + s, record=True)
    return _REC[kind]


if __name__ == "__main__" and "--seeds" in sys.argv:
    for v in (V_WALK, V_RUN):
        s = find_seed(v)
        n = person(v, 0.0, 5000 + s)
        print(f"v={v}: 種 {s} 粒数 {n} 期待 {float(expected(v)):.0f}")


# ---------- 時間割（表示の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
F_INTRO = 2.5                                     # 冒頭の早送り（世界の1秒＝動画の1/2.5秒）。走る人は8秒で100m
TW_RUN = D / V_RUN                                # 走る人が100mに要する秒（20）
TW_WALK = D / V_WALK                              # 歩く人（71.4）
T_R0 = 8.5                                        # 答え合わせ1: 走り出す
R_PH1, R_PH2 = 2.0, 1.7                           # 走る人がゴールするまで／歩く人がゴールするまで（動画の秒）
T_R_RUN = T_R0 + R_PH1
T_R_WALK = T_R_RUN + R_PH2
T_G0 = T_R_WALK + 2.5                             # 1万人へ（≒14.7）
T_D0 = T_G0 + 0.5                                 # 点を打ち始める
D_DUR = 4.0
T_D1 = T_D0 + D_DUR
T_FL = T_D1 + 0.2                                 # 底の赤い線
T_REV = T_FL + 0.7                                # 三択の答え
T_ST2 = T_REV + 0.4                               # 付箋「半分には届かない」
T_S0 = T_ST2 + 2.6                                # 驚き: 上から／前から の棒
S_DUR = 5.2
T_TW = T_S0 + S_DUR                               # ひねり: 追い風
TW_BANNER = 2.3
T_TW_RUN = T_TW + TW_BANNER
TW_DUR = 3.0
T_TW_END = T_TW_RUN + TW_DUR
T_VAL = T_TW_END + 0.2                            # 谷
T_Q = T_VAL + 3.0                                 # 締め
DURATION = T_Q + 3.9

BIG_Q = "雨の中、走ると濡れない？"
DETAIL = "傘なしで100m。1万人でためす"
LABELS = ["半分以下", "少し減る", "変わらない"]


def tau_main(t):
    """答え合わせ1: 動画の時刻 → 世界の秒（走る人が100mを走りきる間はゆっくり、そのあとは早送り）"""
    u = t - T_R0
    if u <= 0:
        return 0.0
    if u < R_PH1:
        return TW_RUN * u / R_PH1
    return min(TW_WALK, TW_RUN + (TW_WALK - TW_RUN) * (u - R_PH1) / R_PH2)


def video_of_tau(tau):
    """tau_main の逆（音を合わせるため）"""
    if tau <= TW_RUN:
        return T_R0 + R_PH1 * tau / TW_RUN
    return T_R0 + R_PH1 + R_PH2 * (tau - TW_RUN) / (TW_WALK - TW_RUN)


def tau_now(t):
    return F_INTRO * t if t < T_GO else tau_main(t)


# ---------- 画面に出す数字（1万人すべて・見本の2人から） ----------

def shown():
    d = data()
    rw, rr = rec("walk"), rec("run")
    nw, nr = rw["n"], rr["n"]
    cut = 1 - nr / nw
    vp, hp, vw, hw = d["vp"], d["hp"], d["vw"], d["hw"]
    m_w, _ = binned_mean(vp, hp, 1.3, 1.5)
    m_r, _ = binned_mean(vp, hp, 4.9, 5.1)
    m_7, _ = binned_mean(vp, hp, 6.8, 7.0 + 1e-9)
    # 追い風の谷: 0.2m/s 幅（1.0, 1.2, ... を中心）ごとの平均の最小
    cen = np.arange(V_LO, V_HI + 1e-9, 0.2)
    means = np.array([hw[(vw >= c - 0.1) & (vw < c + 0.1)].mean() for c in cen])
    k = int(np.argmin(means))
    val_v = float(cen[k])
    m_k = (vw >= val_v - 0.1) & (vw < val_v + 0.1)
    val_exp = float(expected(vw[m_k], WIND).mean())
    return dict(nw=nw, nr=nr, cut=cut, tenths=int(math.floor(cut * 10 + 0.5)),
                walk_top=int(rw["top"].sum()), walk_front=int((~rw["top"]).sum()),
                run_top=int(rr["top"].sum()), run_front=int((~rr["top"]).sum()),
                floor=int(round(floor_hits() / 100.0)) * 100, half=nw / 2,
                cut_run_curve=1 - m_r / m_w, cut_top=1 - m_7 / m_w,
                val_v=val_v, val_n=float(means[k]), val_exp=val_exp, means_w=means)


def fmt_n(n):
    return f"{int(n):,}"


# ---------- 絵: 人（ペン描き風・体に太さのあるラクガキ） ----------
WALK_COL, RUN_COL = "#a9d0f2", "#c5e37a"          # 水色／黄緑のうすい塗り
SKY, ORANGE = "#3a8fd9", "#f29a2e"                # 青＝上から、橙＝前から
PUR, GRN = "#6a4fb3", "#1f9d55"                   # 散布図: 無風／追い風
H_FIG = 185.0


def _limb(ctx, pts, w, col, ink=INK, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink, a))
    for dx, dy in ((0.7, -0.5), (-0.6, 0.8)):
        ctx.set_line_width(w + 4.0)
        ctx.move_to(pts[0][0] + dx, pts[0][1] + dy)
        for p in pts[1:]:
            ctx.line_to(p[0] + dx, p[1] + dy)
        ctx.stroke()
    c = hexrgb(col, a) if isinstance(col, str) else (col[0], col[1], col[2], a)
    ctx.set_source_rgba(*c)
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()


def _dark(col, k=0.82):
    c = hexrgb(col)
    return (c[0] * k, c[1] * k, c[2] * k, 1.0)


def draw_person(ctx, x, gy, h, col, phase, run, amp=1.0, a=1.0):
    """横から見た人（右向き）。足元が (x, gy)。phase は歩調。amp=0 で立ち止まる"""
    if a <= 0:
        return
    s = h / 150.0
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(s, s)
    if a < 1:
        ctx.push_group()
    lean = (0.24 if run else 0.05) * (0.3 + 0.7 * amp)
    A_leg = (0.85 if run else 0.42) * amp
    Kb = 1.55 if run else 0.6
    A_arm = (0.95 if run else 0.42) * amp
    flex = 1.35 if run else 0.3
    bob = (4.5 if run else 1.5) * amp * abs(math.sin(phase))
    hip = (0.0, -72.0 - bob)
    d = (math.sin(lean), -math.cos(lean))
    sh = (hip[0] + 38 * d[0], hip[1] + 38 * d[1])
    hd = (sh[0] + 22 * d[0] + 3, sh[1] + 22 * d[1])

    def leg(j):
        ph = phase + j * math.pi
        a1 = A_leg * math.sin(ph)
        k = Kb * max(0.0, math.cos(ph)) * amp
        knee = (hip[0] + 36 * math.sin(a1), hip[1] + 36 * math.cos(a1))
        b1 = a1 - k
        foot = (knee[0] + 36 * math.sin(b1), knee[1] + 36 * math.cos(b1))
        return [hip, knee, foot, (foot[0] + 10, foot[1] + 1.5)]

    def arm(j):
        ph = phase + (j + 1) * math.pi
        a1 = A_arm * math.sin(ph)
        el = (sh[0] + 22 * math.sin(a1), sh[1] + 22 * math.cos(a1))
        b1 = a1 + flex * (0.35 + 0.65 * amp if run else 1.0) * (1.0 if j == 0 else 0.8)
        hand = (el[0] + 20 * math.sin(b1), el[1] + 20 * math.cos(b1))
        return [sh, el, hand]

    dark = _dark(col)
    # 奥の手足 → 胴と頭 → 手前の手足
    _limb(ctx, leg(1), 17, dark)
    _limb(ctx, arm(1), 12, dark)
    _limb(ctx, [hip, sh], 29, col)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.arc(hd[0], hd[1], 18.3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#fff3df"))
    ctx.arc(hd[0], hd[1], 15.5, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK))                      # 目
    ctx.arc(hd[0] + 8, hd[1] - 2, 2.4, 0, 2 * math.pi)
    ctx.fill()
    _limb(ctx, leg(0), 17, col)
    _limb(ctx, arm(0), 12, col)
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: 雨 ----------
_RNG = np.random.default_rng(4)
N_RAIN = 300
R_X = _RNG.uniform(-20, W + 20, N_RAIN)
R_PH = _RNG.uniform(0, 1000, N_RAIN)
R_SP = _RNG.uniform(650, 1050, N_RAIN)
R_LN = _RNG.uniform(38, 66, N_RAIN)
R_WD = _RNG.uniform(2.2, 3.4, N_RAIN)
R_AL = _RNG.uniform(0.38, 0.8, N_RAIN)
R_FRONT = _RNG.random(N_RAIN) < 0.25
RAIN_COL = "#4f8fd0"


def draw_rain(ctx, t, y0, y1, front, a=1.0, slant=0.0, x0=0.0, x1=float(W), dens=1.0, fade=70.0):
    """縦の雨の線（slant>0 で右へ流れる）。front=True なら手前の層だけ、False なら奥の層だけ"""
    if a <= 0:
        return
    span = y1 - y0
    ctx.save()
    ctx.rectangle(x0, y0, x1 - x0, span)
    ctx.clip()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    r = hexrgb(RAIN_COL)
    sel = np.where(R_FRONT == front)[0]
    sel = sel[:max(1, int(len(sel) * dens))]
    for i in sel:
        yy = y0 + ((R_PH[i] + R_SP[i] * t) % (span + R_LN[i])) - R_LN[i]
        xx = x0 + (R_X[i] % (x1 - x0))
        ym = yy + R_LN[i] / 2
        fd = clamp01(min((ym - y0) / fade, (y1 - ym) / fade)) if fade > 0 else 1.0
        ctx.set_source_rgba(r[0], r[1], r[2], R_AL[i] * a * fd * (0.55 if front else 1.0))
        ctx.set_line_width(R_WD[i])
        ctx.move_to(xx, yy)
        ctx.line_to(xx + slant * R_LN[i], yy + R_LN[i])
        ctx.stroke()
    ctx.restore()


# ---------- 絵: 体に当たった雨粒（色の点） ----------
LAYER_W, LAYER_X0 = 110, -55
LAYER_Y0 = -int(H_FIG) - 22
LAYER_H = int(H_FIG) + 34


class HitLayer:
    """1人ぶんの当たった粒を、体の座標（足元が原点）の画像に点で積む。青＝上から、橙＝前から"""

    def __init__(self, r, seed):
        n = len(r["t"])
        g = np.random.default_rng(seed)
        top = r["top"]
        self.t = r["t"]
        self.top = top
        xt = ((r["xi"] + BL / 2) / BL) * 40 + g.normal(0, 1.0, n)              # 上から: 頭と肩（上半身の上のほう）
        yt = -H_FIG - 6 + g.random(n) * 70
        xf = 0 + g.random(n) * 22                                               # 前から: 体の前側
        yf = -(r["z"] / BH) * H_FIG
        self.px = np.where(top, xt, xf)
        self.py = np.where(top, yt, yf)
        self._off = [(0, 0), (1, 0), (0, 1), (1, 1)]

    def count(self, tau):
        return int(np.searchsorted(self.t, tau, side="right"))

    def image(self, tau, alpha=0.30):
        k = self.count(tau)
        ix = np.round(self.px[:k] - LAYER_X0).astype(np.int64)
        iy = np.round(self.py[:k] - LAYER_Y0).astype(np.int64)
        tp = self.top[:k]
        cov_t = np.zeros(LAYER_W * LAYER_H)
        cov_f = np.zeros(LAYER_W * LAYER_H)
        for dx, dy in self._off:
            x2, y2 = ix + dx, iy + dy
            ok = (x2 >= 0) & (x2 < LAYER_W) & (y2 >= 0) & (y2 < LAYER_H)
            idx = y2 * LAYER_W + x2
            cov_t += np.bincount(idx[ok & tp], minlength=LAYER_W * LAYER_H)
            cov_f += np.bincount(idx[ok & ~tp], minlength=LAYER_W * LAYER_H)
        at = 1 - (1 - alpha) ** cov_t
        af = 1 - (1 - alpha) ** cov_f
        ct, cf = hexrgb(SKY), hexrgb(ORANGE)
        out = np.zeros((LAYER_H, LAYER_W, 4), np.uint8)
        al = (at + af * (1 - at))
        for c, kk in ((2, 0), (1, 1), (0, 2)):
            pm = ct[c] * at + cf[c] * af * (1 - at)
            out[:, :, kk] = (pm.reshape(LAYER_H, LAYER_W) * 255).astype(np.uint8)
        out[:, :, 3] = (al.reshape(LAYER_H, LAYER_W) * 255).astype(np.uint8)
        out = np.ascontiguousarray(out)
        surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, LAYER_W, LAYER_H, LAYER_W * 4)
        return surf, out, k


_LAYERS = {}


def layer(kind):
    if kind not in _LAYERS:
        _LAYERS[kind] = HitLayer(rec(kind), 5 if kind == "walk" else 6)
    return _LAYERS[kind]


# ---------- 世界（雨の道・走る人・歩く人） ----------
X0, X1 = 245.0, 835.0                             # スタート・ゴール（画面のx）
G_RUN_I, G_WALK_I = 660.0, 880.0                  # 冒頭の足元の高さ
G_RUN_M, G_WALK_M = 805.0, 1045.0                 # 答え合わせ1
RAIN_I = (412.0, 905.0)
RAIN_M = (575.0, 1112.0)
STEP_WALK, STEP_RUN = 1.6, 3.0                    # 歩調（1秒に何歩ぶんの周期か。動画の時間）


def layout(t):
    m = INTRO.moved(t)
    lerp = lambda a, b: a + (b - a) * m
    return lerp(G_RUN_I, G_RUN_M), lerp(G_WALK_I, G_WALK_M), lerp(RAIN_I[0], RAIN_M[0]), lerp(RAIN_I[1], RAIN_M[1]), m


def person_alpha(t):
    """冒頭の走りから答え合わせ1へ切り替えるとき、人だけ一瞬消えてスタートへ戻る"""
    if T_GO - 0.15 <= t < T_GO:
        return 1 - ease((t - (T_GO - 0.15)) / 0.15)
    if T_GO <= t < T_GO + 0.25:
        return ease((t - T_GO) / 0.25)
    return 1.0


def prog_of(v, tau):
    return clamp01(v * tau / D)


def draw_world(ctx, t, a=1.0):
    g_run, g_walk, ry0, ry1, m = layout(t)
    tau = tau_now(t)
    pa = person_alpha(t) * a
    # 地面と目印
    for gy in (g_run, g_walk):
        note.pen_line(ctx, 105, gy + 3, 975, gy + 2, INK, seed=int(gy) % 17 + 1, width=4, alpha=0.55 * a)
    for x in (X0 - 12, X1 + 22):
        ctx.set_source_rgba(*hexrgb(RED, 0.8 * a))
        ctx.set_line_width(3)
        ctx.set_dash([8, 7])
        ctx.move_to(x, g_run - 175)
        ctx.line_to(x, g_walk + 14)
        ctx.stroke()
        ctx.set_dash([])
    draw_rain(ctx, t, ry0, ry1, False, a)
    # 人
    for kind, gy, col, v, run, step in (("walk", g_walk, WALK_COL, V_WALK, False, STEP_WALK),
                                         ("run", g_run, RUN_COL, V_RUN, True, STEP_RUN)):
        p = prog_of(v, tau)
        x = X0 + (X1 - X0) * p
        amp = clamp01((1 - p) * D / 2.5)
        if t >= T_GO:
            ctx.push_group()                                   # 体の形の上にだけ点が残る（ATOP）
            draw_person(ctx, x, gy, H_FIG, col, 2 * math.pi * step * t, run, amp, 1.0)
            surf, _keep, k = layer(kind).image(tau)
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ATOP)
            ctx.translate(x, gy)
            ctx.set_source_surface(surf, LAYER_X0, LAYER_Y0)
            ctx.paint()
            ctx.restore()
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(pa)
        else:
            draw_person(ctx, x, gy, H_FIG, col, 2 * math.pi * step * t, run, amp, pa)
    draw_rain(ctx, t, ry0, ry1, True, a)
    # 文字（ラベル）
    text(ctx, "走る人", 78, g_run - 28, 30, INK, align="left", alpha=0.9 * a)
    text(ctx, "歩く人", 78, g_walk - 28, 30, INK, align="left", alpha=0.9 * a)
    if m > 0.5:
        k = (m - 0.5) * 2 * a
        text(ctx, "スタート", X0 - 12, g_walk + 45, 28, INK, bold=False, alpha=k)
        text(ctx, "ゴール", X1 + 22, g_walk + 45, 28, INK, bold=False, alpha=k)
        text(ctx, "← 100m →", (X0 + X1) / 2, g_walk + 45, 28, INK, bold=False, alpha=k)
    # 頭上のカウンター（答え合わせ1）
    if t >= T_GO + 0.1:
        for kind, gy, v in (("run", g_run, V_RUN), ("walk", g_walk, V_WALK)):
            p = prog_of(v, tau)
            x = X0 + (X1 - X0) * p
            n = layer(kind).count(tau)
            s = f"当たった雨粒 {fmt_n(n)}粒"
            sz = 36
            half = core.text_width(s, sz) / 2 + 6
            cx = min(max(x, 72 + half), 1008 - half)
            text(ctx, s, cx, gy - H_FIG - 26, sz, INK, alpha=a * ease_out((t - T_GO - 0.1) / 0.2) * person_alpha(t))


# ---------- 絵: 散布図（本体の座標。紙の中心にそろえるため draw 側で translate(PAGE_DX) する） ----------
PX0, PX1, PY0, PY1 = 215.0, 890.0, 650.0, 1240.0
VMIN, VMAX = 0.5, 7.5
YMAX_A, YMAX_B = 16000.0, 24000.0


def sx(v):
    return PX0 + (np.asarray(v, dtype=float) - VMIN) / (VMAX - VMIN) * (PX1 - PX0)


def sy(h, ymax):
    return PY1 - np.asarray(h, dtype=float) / ymax * (PY1 - PY0)


_OFFS = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 5]
RX0, RY0 = int(PX0) - 10, int(PY0) - 40
RW, RH = int(PX1 - PX0) + 20, int(PY1 - PY0) + 70


def raster_dots(xs, ys, col, alpha=0.5):
    """点を重ねて塗った画像（紙の上なので、重なるほど濃くなる）"""
    ix = np.round(xs - RX0).astype(np.int64)
    iy = np.round(ys - RY0).astype(np.int64)
    cov = np.zeros(RW * RH)
    for dx, dy in _OFFS:
        x2, y2 = ix + dx, iy + dy
        ok = (x2 >= 0) & (x2 < RW) & (y2 >= 0) & (y2 < RH)
        cov += np.bincount((y2 * RW + x2)[ok], minlength=RW * RH)
    al = 1 - (1 - alpha) ** cov
    c = hexrgb(col)
    out = np.zeros((RH, RW, 4), np.uint8)
    for ch, kk in ((2, 0), (1, 1), (0, 2)):
        out[:, :, kk] = (c[ch] * al * 255).reshape(RH, RW).astype(np.uint8)
    out[:, :, 3] = (al * 255).reshape(RH, RW).astype(np.uint8)
    out = np.ascontiguousarray(out)
    return cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, RW, RH, RW * 4), out


_PERM_P = np.random.default_rng(11).permutation(N_PEOPLE)
_PERM_W = np.random.default_rng(12).permutation(N_PEOPLE)


def paint_dots(ctx, kind, k, ymax, col, a):
    d = data()
    v, h, perm = (d["vp"], d["hp"], _PERM_P) if kind == "p" else (d["vw"], d["hw"], _PERM_W)
    idx = perm[:int(k)]
    if len(idx) == 0 or a <= 0:
        return
    surf, _keep = raster_dots(sx(v[idx]), sy(h[idx], ymax), col)
    ctx.set_source_surface(surf, RX0, RY0)
    ctx.paint_with_alpha(a)


def y_ticks(ymax):
    return [(0, "0"), (5000, "5千"), (10000, "1万"), (15000, "1.5万")] if ymax < 20000 else \
        [(0, "0"), (10000, "1万"), (20000, "2万")]


def draw_axes(ctx, ymax_t, a, red_tick=None):
    if a <= 0:
        return
    e = ease((ymax_t - YMAX_A) / (YMAX_B - YMAX_A))
    ymax = YMAX_A + (YMAX_B - YMAX_A) * e
    note.pen_line(ctx, PX0 - 6, PY0 - 10, PX0 - 6, PY1 + 3, INK, seed=3, width=4.5, alpha=0.85 * a)
    note.pen_line(ctx, PX0 - 6, PY1 + 3, PX1 + 10, PY1 + 3, INK, seed=4, width=4.5, alpha=0.85 * a)
    for which, al in ((0, 1 - e), (1, e)):
        for val, lab in y_ticks(YMAX_A if which == 0 else YMAX_B):
            yy = float(sy(val, ymax))
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * al))
            ctx.set_line_width(3)
            ctx.move_to(PX0 - 14, yy)
            ctx.line_to(PX0 - 6, yy)
            ctx.stroke()
            text(ctx, lab, PX0 - 20, yy, 28, INK, align="right", bold=False, alpha=a * al)
    for v in range(1, 8):
        xx = float(sx(v))
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, PY1 + 3)
        ctx.line_to(xx, PY1 + 12)
        ctx.stroke()
        text(ctx, str(v), xx, PY1 + 34, 28, RED if red_tick == v else INK, bold=red_tick == v, alpha=a)
    text(ctx, "ゆっくり歩き", PX0 + 5, PY1 + 78, 28, INK, align="left", bold=False, alpha=a)
    text(ctx, "全力疾走", PX1, PY1 + 78, 28, INK, align="right", bold=False, alpha=a)
    text(ctx, "進む速さ（m/s）", (PX0 + PX1) / 2, PY1 + 118, 30, INK, bold=False, alpha=a)
    text(ctx, "当たった雨粒（粒）", PX0 - 95, PY0 - 28, 28, INK, align="left", bold=False, alpha=a)


def pen_arrow(ctx, x0, y0, x1, y1, color, seed, width=6, alpha=1.0):
    note.pen_line(ctx, x0, y0, x1, y1, color, seed=seed, width=width, alpha=alpha)
    ang = math.atan2(y1 - y0, x1 - x0)
    for sgn in (-1, 1):
        a2 = ang + math.pi + sgn * 0.5
        note.pen_line(ctx, x1, y1, x1 + 24 * math.cos(a2), y1 + 24 * math.sin(a2), color, seed=seed + 3 * sgn,
                      width=width, alpha=alpha)


def number_row(ctx, parts, y, a, size=44, cx=540):
    ws = [core.text_width(s, size) for s, _ in parts]
    x = cx - sum(ws) / 2
    for (s, col), w in zip(parts, ws):
        text(ctx, s, x, y, size, col, align="left", alpha=a)
        x += w


# ---------- 絵: 棒（上から／前から） ----------
BAR_Y, BAR_K = 1240.0, 480.0 / 16000.0
BAR_X = {"walk": 360.0, "run": 700.0}
BAR_W = 200.0


def draw_bars(ctx, t, a):
    sh = shown()
    note.pen_line(ctx, 215, BAR_Y + 3, 890, BAR_Y + 2, INK, seed=8, width=4.5, alpha=0.85 * a)
    e_f = ease_out((t - (T_S0 + 0.6)) / 0.8)
    e_t = ease_out((t - (T_S0 + 1.6)) / 1.0)
    for kind, lab in (("walk", "歩く人"), ("run", "走る人")):
        cx = BAR_X[kind]
        nf = sh[kind + "_front"]
        nt = sh[kind + "_top"]
        hf = nf * BAR_K * e_f
        ht = nt * BAR_K * e_t
        for (y0, hh, col) in ((BAR_Y - hf, hf, ORANGE), (BAR_Y - hf - ht, ht, SKY)):
            if hh <= 0.5:
                continue
            ctx.set_source_rgba(*hexrgb(col, 0.78 * a))
            ctx.rectangle(cx - BAR_W / 2, y0, BAR_W, hh)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
            ctx.set_line_width(4)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.rectangle(cx - BAR_W / 2, y0, BAR_W, hh)
            ctx.stroke()
        if t >= T_S0 + 2.7:
            b = ease_out((t - T_S0 - 2.7) / 0.3) * a
            text(ctx, fmt_n(nf), cx, BAR_Y - nf * BAR_K / 2, 32, INK, alpha=b)
            text(ctx, fmt_n(nt), cx, BAR_Y - nf * BAR_K - nt * BAR_K / 2, 32, INK, alpha=b)
            text(ctx, f"合計 {fmt_n(nf + nt)}粒", cx, BAR_Y - (nf + nt) * BAR_K - 30, 34, INK, alpha=b)
        text(ctx, lab, cx, BAR_Y + 40, 36, INK, alpha=a)
    if t >= T_S0 + 2.7:
        b = ease_out((t - T_S0 - 2.7) / 0.3) * a
        note.legend(ctx, [(SKY, "上から＝時間に比例"), (ORANGE, "前から＝距離で決まる")], 1330, 28)


# ---------- 絵: 追い風の枠 ----------
WX0, WX1, WY0, WY1 = 640.0, 890.0, 660.0, 815.0


def draw_wind_inset(ctx, t, a):
    if a <= 0:
        return
    draw_rain(ctx, t, WY0, WY1, False, a, slant=WIND / U, x0=WX0, x1=WX1, dens=0.3, fade=0)
    draw_rain(ctx, t, WY0, WY1, True, a, slant=WIND / U, x0=WX0, x1=WX1, dens=0.3, fade=0)
    for (xa, ya, xb, yb, sd) in ((WX0, WY0, WX1, WY0 + 2, 91), (WX1, WY0, WX1 + 2, WY1, 92),
                                 (WX1, WY1, WX0, WY1 + 2, 93), (WX0, WY1, WX0 - 2, WY0, 94)):
        note.pen_line(ctx, xa, ya, xb, yb, PENCIL, seed=sd, width=3, alpha=0.7 * a)
    draw_person(ctx, 835, WY1 - 6, 92, RUN_COL, 2 * math.pi * STEP_RUN * t, True, 1.0, a)
    pen_arrow(ctx, WX0 + 14, WY0 + 34, WX0 + 100, WY0 + 34, GRN, 7, width=6, alpha=a)
    text(ctx, "追い風 3m/s", WX0 + 4, WY0 - 20, 30, GRN, align="left", alpha=a)


# ---------- 冒頭・上のブロック ----------

class AIntro(note.Intro):
    """この回だけの冒頭。上半分に雨の道（0秒目から雨が降り、2人が動き出す）、下に大きな問い"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL                              # 音（ベル）を前提の行に合わせる
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 64
        w = core.text_width(BIG_Q, sz)
        if w > 860:
            sz *= 860 / w
            w = 860
        text(ctx, BIG_Q, 570, 960, sz, INK, alpha=a)
        note.pen_line(ctx, 570 - w / 2 - 6, 1007, 570 + w / 2 + 6, 1001, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 1070, 36, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            y = 1160 + i * 88
            x0 = self.LX + 38 + 14 * (1 - show)
            note.pen_circle(ctx, x0, y, 34, 34, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0, y, 44, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, y, 56, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            note.hand_text(ctx, "予想して！", 775, 1155, 52, RED, seed=41, alpha=a2, align="center")
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            note.pen_circle(ctx, 785, 1272, 72, 68, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(785, 1272)
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
            cx, y = 540 + (i - 1) * 290, 520
            ok = i == self.correct
            a = m * (1 - 0.55 * rev * (not ok))
            vs = 46
            vw = core.text_width(v, vs)
            if 64 + vw > 252:                           # 右端が iPhone で切れない幅（紙の中心 +40 を含めて x≤1010）まで
                vs *= (252 - 64) / vw
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


INTRO = AIntro(["雨の中、", "走ると濡れない？"], LABELS, correct=1, msg="", rule=None)


# ---------- 本体 ----------

def ymax_at(t):
    return YMAX_A + (YMAX_B - YMAX_A) * ease((t - (T_TW + 0.3)) / 1.0)


def body(ctx, t):
    sh = shown()
    # --- 答え合わせ1: 色の点・結果
    if T_GO + 0.3 <= t < T_G0 + 0.3:
        out = 1 - ease((t - T_G0) / 0.3)
        k = ease_out((t - T_GO - 0.3) / 0.3) * out
        note.legend(ctx, [(RUN_COL, "走る人 時速18km"), (WALK_COL, "歩く人 時速5km")], 1155, 28)
        ctx.save()
        ctx.translate(0, 0)
        note.legend(ctx, [(SKY, "青＝上から当たった"), (ORANGE, "橙＝前から当たった")], 1212, 28)
        ctx.restore()
        if t >= T_R_RUN + 0.1:
            b = ease_out((t - T_R_RUN - 0.1) / 0.3) * out
            number_row(ctx, [("走る人 ", INK), (fmt_n(sh["nr"]), "#4f8a1f"), ("粒", INK)], 1282, b, size=46)
        if t >= T_R_WALK + 0.1:
            b = ease_out((t - T_R_WALK - 0.1) / 0.3) * out
            number_row(ctx, [("歩く人 ", INK), (fmt_n(sh["nw"]), "#2f62c9"), ("粒", INK)], 1348, b, size=46)
        if t >= T_R_WALK + 0.4:
            b = ease_out((t - T_R_WALK - 0.4) / 0.3) * out
            number_row(ctx, [("走ると 約", RED), (f"{sh['tenths']}", RED), ("割減", RED)], 1412, b, size=50)
    # --- 答え合わせ2: 1万人の散布図
    ca = 0.0
    if T_G0 <= t < T_S0 + 0.3:
        ca = ease((t - T_G0) / 0.3) * (1 - ease((t - T_S0) / 0.3))
    elif T_TW <= t < T_Q + 1:
        ca = ease((t - T_TW) / 0.3) * (1 - 0.55 * ease_out((t - T_Q) / 0.35))
    if ca > 0:
        ym = ymax_at(t) if t >= T_TW else YMAX_A
        draw_axes(ctx, ym, ca, red_tick=3 if (t >= T_VAL) else None)
        wind_scene = t >= T_TW
        kp = N_PEOPLE * clamp01((t - T_D0) / D_DUR) if not wind_scene else N_PEOPLE
        ghost = 1.0 - 0.62 * ease((t - T_TW) / 0.4) if wind_scene else 1.0
        paint_dots(ctx, "p", kp, ym, PUR, ca * ghost)
        if wind_scene and t >= T_TW_RUN:
            kw = N_PEOPLE * clamp01((t - T_TW_RUN) / TW_DUR)
            paint_dots(ctx, "w", kw, ym, GRN, ca)
        # 歩く人の半分の線（赤）。2026-10-07 ユーザー「底より下はない、がよくわからない」→ 底の線をやめ、問いの「半分」に結びつける
        if not wind_scene and t >= T_FL:
            b = ease_out((t - T_FL - 0.3) / 0.3) * ca
            hy = float(sy(sh["half"], ym))
            ctx.set_source_rgba(*hexrgb(RED, 0.9 * b))
            ctx.set_line_width(5)
            ctx.set_dash([16, 10])
            ctx.move_to(PX0, hy)
            ctx.line_to(PX1, hy)
            ctx.stroke()
            ctx.set_dash([])
            text(ctx, f"歩く人の半分（{fmt_n(sh['half'])}粒）", PX1, hy + 34, 30, RED, align="right", alpha=b)
        # 見本の2人の印
        if not wind_scene and t >= T_FL:
            b = ease_out((t - T_FL) / 0.3) * ca
            for v, n, lab, sd in ((V_WALK, sh["nw"], "歩く人", 61), (V_RUN, sh["nr"], "走る人", 62)):
                px, py = float(sx(v)), float(sy(n, ym))
                note.pen_circle(ctx, px, py, 22, 22, INK, seed=sd, width=4, alpha=b, progress=clamp01((t - T_FL) / 0.5))
                text(ctx, lab, px + 70, py - 32, 30, INK, alpha=b)
        if not wind_scene:
            if t < T_FL:
                kk = int(kp)
                number_row(ctx, [("ためした人 ", INK), (fmt_n(kk), PUR), (" / 10,000人", INK)], 1410, ca, size=38)
            if t >= T_ST2:
                b = ease_out((t - T_ST2) / 0.3) * ca
                note.sticky(ctx, "全力で走っても\n半分には届かない", 540, 1125, 42, "pink", fg=RED, a=b, tilt=-0.015)
        # 追い風
        if wind_scene:
            if t < T_TW_RUN:
                a = ease_out((t - T_TW) / 0.25) * ca
                note.banner(ctx, "追い風だったら？", 520, 715, a=a, t_rel=t - T_TW, size=56)
            else:
                draw_wind_inset(ctx, t, ease_out((t - T_TW_RUN + 0.2) / 0.3) * ca)
            if T_TW_RUN <= t:
                kk = int(N_PEOPLE * clamp01((t - T_TW_RUN) / TW_DUR))
                if t < T_VAL:
                    number_row(ctx, [("追い風で ", INK), (fmt_n(kk), GRN), (" / 10,000人", INK)], 1410, ca, size=36)
            if t >= T_VAL:
                b = ease_out((t - T_VAL) / 0.3) * ca
                vx, vy = float(sx(sh["val_v"])), float(sy(sh["val_n"], YMAX_B))
                note.pen_circle(ctx, vx, vy, 36, 28, RED, seed=71, width=6, alpha=b, progress=clamp01((t - T_VAL) / 0.5))
                ctx.set_source_rgba(*hexrgb(RED, 0.7 * b))
                ctx.set_line_width(3)
                ctx.set_dash([7, 8])
                ctx.move_to(vx, vy - 30)
                ctx.line_to(vx, vy - 150)
                ctx.stroke()
                ctx.set_dash([])
                if t < T_Q + 0.35:
                    note.sticky(ctx, "風と同じ速さが\nいちばん濡れない", 560, 890, 40, "mint", a=b * (1 - ease_out((t - T_Q) / 0.35)),
                                tilt=-0.015)
    # --- 驚き: 上から／前から の棒
    if T_S0 <= t < T_TW + 0.3:
        out = 1 - ease((t - T_TW) / 0.3)
        ba = ease((t - T_S0) / 0.3) * out
        draw_bars(ctx, t, ba)
        b = ease_out((t - T_S0 - 0.2) / 0.3) * out
        note.sticky(ctx, "全力で走っても、\n前から当たる分は減らない", 540, 690, 44, "pink", fg=RED, a=b, tilt=-0.015)
    # --- 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "なんで全力で走っても、\n半分にもならないの？", 520, 715, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 520, 905, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    wa = 1 - ease((t - T_G0) / 0.3) if t >= T_G0 else 1.0
    if wa > 0:
        draw_world(ctx, t, wa)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    body(ctx, t)
    ctx.restore()


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


def rain_sound(dur, seed=1):
    """うるさくない雨音: 600Hz〜6kHz に絞ったノイズに、ゆっくりした強弱"""
    x = band_noise(dur, 600.0, 6500.0, seed, 0.030)
    tt = np.arange(len(x)) / SR
    env = 0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * tt + 1.0) * np.sin(2 * np.pi * 0.071 * tt + 0.3)
    fade = np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.6)
    return x * env * fade


def wind_sound(dur, seed=2):
    x = band_noise(dur, 80.0, 700.0, seed, 0.06, 80.0, 500.0)
    tt = np.arange(len(x)) / SR
    env = np.sin(np.pi * np.clip(tt / dur, 0, 1)) ** 1.5
    return x * (0.4 + 0.6 * env)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    # 雨音（1万人の場面は小さく）
    r = rain_sound(DURATION)
    tt = np.arange(len(r)) / SR
    gain = np.where(tt < T_G0, 1.0, np.where(tt < T_TW, 0.45, 0.6))
    mx.add(0, r * gain, 1.0, bgm=True)
    INTRO.audio(mx)
    # 冒頭〜答え合わせ1
    mx.add(T_GO + 0.1, blip(880.0, 0.2), 0.25)
    mx.add(T_R_RUN, blip(1046.5, 0.25), 0.45)                       # 走る人がゴール
    mx.add(T_R_WALK, blip(784.0, 0.25), 0.45)                       # 歩く人がゴール
    for kind, f0 in (("run", 2400.0), ("walk", 1700.0)):
        lay = layer(kind)
        rng = np.random.default_rng(3 if kind == "run" else 4)
        step = 0.06
        tt0 = T_R0
        while tt0 < T_R_WALK:
            n = lay.count(tau_main(tt0 + step)) - lay.count(tau_main(tt0))
            if n > 0:
                mx.add(tt0, tick(float(rng.uniform(f0, f0 * 1.5)), 0.03), 0.02 + 0.05 * min(1.0, n / 120))
            tt0 += step
    # 1万人
    mx.add(T_G0 - 0.5, riser(0.9), 0.5)
    beat(mx, T_D0, T_D1, bpm=124, vol=0.5, accel=True)
    d = data()
    rng = np.random.default_rng(5)
    for b in range(int(D_DUR * 8)):
        mx.add(T_D0 + b / 8, tick(float(rng.uniform(1700, 3300)), 0.03), 0.05 + 0.04 * (b / (D_DUR * 8)))
    mx.add(T_FL, thump(), 0.6)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST2, blip(659.3, 0.15), 0.35)
    # 驚き
    mx.add(T_S0 + 0.2, bell(880.0, 1.0), 0.35)
    mx.add(T_S0 + 0.6, blip(523.3, 0.2), 0.35)
    mx.add(T_S0 + 1.6, blip(784.0, 0.2), 0.35)
    mx.add(T_S0 + 2.7, chord([261.6, 329.6, 392.0], 1.4), 0.4)
    # 追い風
    mx.add(T_TW, riser(0.8), 0.45)
    mx.add(T_TW, wind_sound(T_TW_END + 1.0 - T_TW), 1.0, bgm=True)
    beat(mx, T_TW_RUN, T_TW_END, bpm=140, vol=0.45)
    for b in range(int(TW_DUR * 8)):
        mx.add(T_TW_RUN + b / 8, tick(float(rng.uniform(1700, 3300)), 0.03), 0.05)
    mx.add(T_VAL, thump(), 0.6)
    mx.add(T_VAL + 0.1, bell(1046.5, 1.6), 0.5)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    d = data()
    vp, hp, vw, hw, vq, hq = d["vp"], d["hp"], d["vw"], d["hw"], d["vq"], d["hq"]
    sh = shown()
    ep, ew = expected(vp), expected(vw, WIND)
    zp, zw = (hp - ep) / np.sqrt(ep), (hw - ew) / np.sqrt(ew)
    checks = []
    for v, w, n, mean, exact, se in d["loose"]:
        checks.append((f"力ずくで数えた平均 v={v:.1f}m/s 風{w:.0f}m/s（粒） vs 理論値", float(mean), float(exact), max(4 * float(se), 0.004 * float(exact))))
    checks += [
        ("速い数え方 無風1万人: 理論値からのずれの平均（粒）", float((hp - ep).mean()), 0.0, 4.0),
        ("速い数え方 追い風1万人: 理論値からのずれの平均（粒）", float((hw - ew).mean()), 0.0, 4.0),
        ("無風: ずれ÷√理論値 の分散（ポアソンなら1）", float(zp.var()), 1.0, 0.05),
        ("追い風: ずれ÷√理論値 の分散（ポアソンなら1）", float(zw.var()), 1.0, 0.05),
        ("無風の1万人は全員が「底」（前から当たる分）より上", float((hp >= floor_hits()).all()), 1.0, 0.0),
        ("追い風の谷の速さ（m/s）が風の速さ", sh["val_v"], WIND, 0.15),
        ("追い風の谷の高さ（粒）が理論値（同じ範囲の速さの人の期待値の平均）", sh["val_n"], sh["val_exp"], 0.03 * sh["val_exp"]),
        ("追い風の谷は無風の底より低い", float(sh["val_n"] < floor_hits()), 1.0, 0.0),
        ("画面の「歩く人」の粒数は理論値から標準偏差の0.5倍以内", float(abs(sh["nw"] - float(expected(V_WALK))) < 0.5 * math.sqrt(float(expected(V_WALK)))), 1.0, 0.0),
        ("画面の「走る人」の粒数は理論値から標準偏差の0.5倍以内", float(abs(sh["nr"] - float(expected(V_RUN))) < 0.5 * math.sqrt(float(expected(V_RUN)))), 1.0, 0.0),
        ("画面の「○割減」（見本の2人 vs 理論値）が同じ丸め", float(sh["tenths"]), float(math.floor((1 - expected(V_RUN) / expected(V_WALK)) * 10 + 0.5)), 0.0),
        ("画面の「○割減」（1万人の曲線から）が同じ丸め", float(math.floor(sh["cut_run_curve"] * 10 + 0.5)), float(sh["tenths"]), 0.0),
        ("画面の「底」約○粒が、別の乱数の1万人の最小付近と整合（7m/s付近の平均 > 底）", float(binned_mean(vq, hq, 6.8, 7.1)[0] > sh["floor"]), 1.0, 0.0),
        ("答えは B: 全力でも半分以下にならない（最大の減り方 < 50%）", float(sh["cut_top"] < 0.5), 1.0, 0.0),
        ("答えは B: 走ると1割以上は減る", float(sh["cut_run_curve"] > 0.10), 1.0, 0.0),
        ("見本の2人の上／前の内訳が理論値に近い（歩く人の前から、標準偏差の4倍以内）",
         float(abs(sh["walk_front"] - NDENS * A_FRONT * D) < 4 * math.sqrt(NDENS * A_FRONT * D)), 1.0, 0.0),
        ("見本の2人の「前から」は速さによらず同じ（粒、標準偏差の4倍以内）",
         float(abs(sh["walk_front"] - sh["run_front"]) < 4 * math.sqrt(2 * NDENS * A_FRONT * D)), 1.0, 0.0),
    ]
    check_answers(checks)


if __name__ == "__main__" and "--compute" not in sys.argv and "--seeds" not in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    d = data()
    sh = shown()
    print(f"見本の種 歩く={WALK_SEED} 走る={RUN_SEED} / 長さ={DURATION:.1f}秒")
    print(f"歩く人 {sh['nw']}粒（上 {sh['walk_top']} 前 {sh['walk_front']}）／走る人 {sh['nr']}粒（上 {sh['run_top']} 前 {sh['run_front']}）"
          f"／減った割合 {sh['cut'] * 100:.1f}%（○割={sh['tenths']}）")
    print(f"1万人の曲線: 1.4→5m/s で {sh['cut_run_curve'] * 100:.1f}%減、1.4→7m/s で {sh['cut_top'] * 100:.1f}%減／底 {floor_hits():.0f}粒")
    print(f"追い風の谷: {sh['val_v']:.2f}m/s あたりで平均 {sh['val_n']:.0f}粒（同じ範囲の期待値 {sh['val_exp']:.0f}、谷の底の理論値 {float(expected(WIND, WIND)):.0f}）")
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 12.0, 15.0, 18.0, 21.0, 24.0, 27.0, 30.0, 33.0, 36.0, 39.0]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
