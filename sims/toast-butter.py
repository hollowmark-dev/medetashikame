"""トーストを落とすと、バターが下？ テーブルと高い棚から1万枚ずつ。— 2026-10-11 作成（公開予定 10/12）

モデル（横から見た2次元。トーストは厚みのある固い板、バターの重さは無視）
  1. すべり出し : トーストがテーブルの上をすべり、重心がテーブルの角を越えたときの速さ v0（そっと押した＝0.02〜0.4 m/s）。
  2. 角の上で回る: 角を支点に傾きはじめる。角との間の摩擦が足りているあいだは「すべらずに回る」、
                   足りなくなったら（必要な摩擦 > 静止摩擦係数×押す力）角の上をすべりながら回る（動摩擦）。
                   角が板を押す力が0になったところ（または板の端が角を越えたところ）で角から離れる。
                   運動方程式は Bacon, Heald & James (2001) と同じ形（厚みは慣性モーメントにだけ入れる）。
  3. 自由落下   : 離れたときの回転の速さのまま回りながら落ちる（空気抵抗なし）。
  4. 着地       : 板のいちばん低い角（板の大きさ・厚みを入れる）が床に着いた瞬間の回転角で、上下を決める。
                   回った角度が 90°〜270°（＋1回転ごと）ならバターが下。はねる・すべるは考えない（Bacon らも砂で止めて数えた）。
  1枚ごとの違い: 押した速さ v0（0.02〜0.4 m/s）、静止摩擦係数 μs（0.25〜0.65）、動摩擦 μk＝μs×(0.70〜0.80)、
                 一辺 10〜12cm、厚さ 1.2〜2.0cm、高さ（テーブル 0.71〜0.79m／高い棚 1.76〜1.84m）。すべて一様乱数。
                 μs の幅は、Matthews (1995) のトースト 0.25 と Bacon ら (2001) のトーストの角 0.62 を両端に含める。

問い: 「バターの面が下になるのは、気のせい？」（2026-10-11 ユーザー選定） A 気のせい ／ B 7割くらい ／ C 9割以上。
      答えは C（テーブルから、そっと押したら、ほぼ毎回バターが下）。ひねり＝高い棚（1.8m）だと逆転してバターが上のほうが多い。
見せ方: 冒頭＝高さのちがう家具（テーブル75cm・カウンター1m・高い棚1.8m）から0秒目にトーストが次々と落ちる（床のずっと上で消える）。マス目はシミュから。
        シミュ＝テーブルと高い棚が並んで、手でそっと押す見本1枚ずつ → 1万枚ずつ（マス目がバターが下＝赤／上＝黄で埋まる）。
        驚き＝床に着くまでに回った角度のヒストグラム（テーブルはちょうど半回転）。ひねり＝高い棚は回りすぎる。
        締め＝「バターが重いから下になるの？ → 答えは概要欄に」。

照合（check_answers）:
 (1) Bacon ら (2001) の実験値: 板（10.2cm・厚さ1.3cm・μs=0.32・μk=0.24）を置いた位置からの落下の、回る速さ（表I・10点）と
     76cm からの上下（表II・17点）を、同じモデルで再現できる
 (2) すべらない場合（摩擦を大きく）の回る速さが、閉じた式 ω² = 6gδ sinθ /(a²+3δ²)（Matthews 1995 / Bacon ら 式14）と一致
 (3) 着地の判定（時間を細かく刻んだ探索）が、二分法で解いた着地時刻・角度と一致
 (4) 時間の刻みを半分にしても、上下の判定がほぼ変わらない
 (5) 画面の%が、別の乱数で2万枚ずつ落とした値と同じ丸め
 (6) 答えは C（テーブルで 90% 以上がバターが下）、ひねり（高い棚で 50% を下回る）
乱数の種は見本の見栄えのために選んでよい。画面の統計は1万枚すべてから正直に出す。
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
note.DATE = "10.12"                               # 日付欄（公開予定日）

SLUG = "toast-butter"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
G = 9.81
N_SLICE = 10000
N_REF = 20000                                     # 丸めの照合用（別の乱数）
V0 = (0.02, 0.40)                                 # 重心が角を越えるときの速さ（m/s）。そっと押した
MUS = (0.25, 0.65)                                # 静止摩擦係数
MUK_R = (0.70, 0.80)                              # 動摩擦÷静止摩擦（Bacon ら: 0.24/0.32 = 0.75）
SIDE = (0.10, 0.12)                               # 一辺（m）
THICK = (0.012, 0.020)                            # 厚さ（m）
HEIGHTS = {"table": (0.71, 0.79), "shelf": (1.76, 1.84)}
H_LABEL = {"table": 0.75, "shelf": 1.8}
DT = 2e-5                                         # 角の上の運動の時間の刻み（s）


def params(n, seed, surf):
    rng = np.random.default_rng(seed)
    v0 = rng.uniform(*V0, n)
    mus = rng.uniform(*MUS, n)
    muk = mus * rng.uniform(*MUK_R, n)
    a = rng.uniform(*SIDE, n) / 2
    b = rng.uniform(*THICK, n)
    h = rng.uniform(*HEIGHTS[surf], n)
    return dict(v0=v0, mus=mus, muk=muk, a=a, b=b, h=h)


def edge_phase(v0, mus, muk, a, b, s0=None, dt=DT, record_every=0, tmax=3.0):
    """テーブルの角の上の運動。s＝角から重心までの板に沿った距離、th＝傾き（外側が下がる向きが正）。
    返り値: 角を離れたときの状態（重心の位置・速度は角を原点、上が正）。record_every>0 なら途中の (t, s, th) も返す"""
    n = len(v0)
    s = np.zeros(n) if s0 is None else np.array(s0, float)
    sd = np.array(v0, float)
    th = np.zeros(n)
    thd = np.zeros(n)
    k2 = (4 * a * a + b * b) / 12                 # 重心まわりの慣性モーメント÷質量
    stick = sd <= 0
    on = np.ones(n, bool)
    slipped = np.zeros(n, bool)
    out = {k: np.zeros(n) for k in ("th", "thd", "x", "y", "vx", "vy", "t")}
    hist = []
    t, step = 0.0, 0
    while on.any() and t < tmax:
        c, si = np.cos(th), np.sin(th)
        # すべらずに回る（s 一定）
        thdd_st = G * s * c / (k2 + s * s)
        n_st = G * c - s * thdd_st
        f_st = -(G * si + s * thd ** 2)           # 要る摩擦（板に沿う向き、質量あたり）
        go = stick & (np.abs(f_st) > mus * np.maximum(n_st, 1e-12))
        stick &= ~go
        slipped |= go
        # すべりながら回る（動摩擦）
        thdd_sl = s * (G * c - 2 * sd * thd) / (k2 + s * s)
        n_sl = G * c - 2 * sd * thd - s * thdd_sl
        sdd_sl = s * thd ** 2 + G * si - muk * np.where(sd < 0, -1.0, 1.0) * n_sl
        thdd = np.where(stick, thdd_st, thdd_sl)
        nf = np.where(stick, n_st, n_sl)
        sdd = np.where(stick, 0.0, sdd_sl)
        off = on & ((nf <= 0) | (s >= a))         # 押す力が0、または板の端が角を越えた
        if off.any():
            out["th"][off], out["thd"][off] = th[off], thd[off]
            out["x"][off], out["y"][off] = (s * c)[off], (-s * si)[off]
            out["vx"][off] = (sd * c - s * thd * si)[off]
            out["vy"][off] = (-sd * si - s * thd * c)[off]
            out["t"][off] = t
            on &= ~off
        if record_every and step % record_every == 0:
            hist.append((t, s.copy(), th.copy()))
        thd = thd + thdd * dt * on
        sdn = sd + sdd * dt * on
        halt = (~stick) & (sd > 0) & (sdn <= 0)   # すべりが止まった → また止まって回る
        sdn = np.where(halt, 0.0, sdn)
        stick |= halt
        sd = sdn
        s = s + sd * dt * on
        th = th + thd * dt * on
        t += dt
        step += 1
    out["slipped"] = slipped
    if record_every:
        hist.append((t, s.copy(), th.copy()))
        out["hist_t"] = np.array([h[0] for h in hist])
        out["hist_s"] = np.array([h[1] for h in hist])
        out["hist_th"] = np.array([h[2] for h in hist])
    return out


def low_point(o, a, b, t):
    """離れてから t 秒後の、板のいちばん低い点の高さ（角＝0、上が正）"""
    y = o["y"] + o["vy"] * t - 0.5 * G * t * t
    th = o["th"] + o["thd"] * t
    return y - a * np.abs(np.sin(th)) - b / 2 * np.abs(np.cos(th))


def landing(o, a, b, h, dt=1e-4):
    """床（角から h 下）に最初に触れる時刻と、そのときの回転角"""
    n = len(o["th"])
    tl = np.full(n, np.nan)
    done = np.zeros(n, bool)
    t = 0.0
    while not done.all():
        hit = (~done) & (low_point(o, a, b, t) <= -h)
        tl[hit] = t
        done |= hit
        t += dt
    # 刻みの間を二分法で詰める
    lo, hi = np.maximum(tl - dt, 0.0), tl
    for _ in range(20):
        mid = (lo + hi) / 2
        below = low_point(o, a, b, mid) <= -h
        hi = np.where(below, mid, hi)
        lo = np.where(below, lo, mid)
    tl = hi
    return tl, o["th"] + o["thd"] * tl


def butter_down(rot):
    m = np.mod(rot, 2 * np.pi)
    return (m > np.pi / 2) & (m < 1.5 * np.pi)


def _run(args):
    surf, n, seed = args
    p = params(n, seed, surf)
    o = edge_phase(p["v0"], p["mus"], p["muk"], p["a"], p["b"])
    tl, rot = landing(o, p["a"], p["b"], p["h"])
    return dict(**p, t_off=o["t"], th_off=o["th"], w=o["thd"], x_off=o["x"], y_off=o["y"],
                vx=o["vx"], vy=o["vy"], slipped=o["slipped"], t_land=tl, rot=rot)


def run_many(surf, n, seed, chunk=1250):
    jobs = [(surf, min(chunk, n - i), seed * 1000 + i // chunk) for i in range(0, n, chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        parts = list(ex.map(_run, jobs))
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


SEEDS = {"table": 1, "shelf": 2, "table_ref": 101, "shelf_ref": 102}


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    z = {}
    for key, seed in SEEDS.items():
        surf = key.split("_")[0]
        n = N_REF if key.endswith("ref") else N_SLICE
        d = run_many(surf, n, seed)
        for k, v in d.items():
            z[f"{key}__{k}"] = v
        print(f"  {key}: {n}枚 バターが下 {butter_down(d['rot']).mean() * 100:.2f}%")
    np.savez(OUT / "data.npz", **z)


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = OUT / "data.npz"
        if not f.exists():
            compute()
        z = np.load(f)
        _DATA = {}
        for k in z.files:
            key, name = k.split("__")
            _DATA.setdefault(key, {})[name] = z[k]
    return _DATA


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def shown():
    d = data()
    out = {}
    for s in ("table", "shelf"):
        dn = butter_down(d[s]["rot"])
        out[s + "_n"] = int(dn.sum())
        out[s + "_p"] = dn.mean()
        out[s + "_pct"] = pct(dn.mean())
        out[s + "_ref"] = butter_down(d[s + "_ref"]["rot"]).mean()
        out[s + "_rot_med"] = float(np.degrees(np.median(d[s]["rot"])))
    return out


if __name__ == "__main__" and "--compute" in sys.argv:
    import time
    t0 = time.time()
    compute()
    print(f"計算 {time.time() - t0:.0f}秒")


# ---------- 見本の1枚（テーブル・棚） ----------
def typical(surf):
    """見本: 回った角度がその高さの中央値にいちばん近く、押した速さが中くらいの1枚（見栄えのための選び方）"""
    d = data()[surf]
    med = np.median(d["rot"])
    score = np.abs(d["rot"] - med) + 2.0 * np.abs(d["v0"] - 0.2)
    return int(np.argmin(score))


_TRAJ = {}


def traj_indices(surf):
    """絵に使う1枚ずつの番号（見本・1万枚の場面の代表・冒頭の飾り）"""
    idx = {typical(surf)} | set(range(FAST_K))
    idx |= {j for (_i, _r, _t0, j) in deco_jobs()}      # 冒頭の飾り（テーブル・棚は自分の1万枚の値）

    return sorted(idx)


def _traj_batch(surf):
    """絵に使う枚数ぶんの動きを、まとめて記録し直す（同じ値・同じ刻みなので、1万枚の結果と同じになる）"""
    d = data()[surf]
    sel = np.array(traj_indices(surf))
    f = OUT / f"traj_{surf}.npz"
    if f.exists():
        z = np.load(f)
        if np.array_equal(z["sel"], sel):
            return {k: z[k] for k in z.files}
    o = edge_phase(d["v0"][sel], d["mus"][sel], d["muk"][sel], d["a"][sel], d["b"][sel], record_every=25)
    tl, rot = landing(o, d["a"][sel], d["b"][sel], d["h"][sel])
    z = dict(sel=sel, ht=o["hist_t"], hs=o["hist_s"], hth=o["hist_th"], t_off=o["t"], th=o["th"], w=o["thd"],
             x=o["x"], y=o["y"], vx=o["vx"], vy=o["vy"], t_land=tl, rot=rot)
    np.savez(f, **z)
    return z


def traj(surf, idx):
    key = (surf, idx)
    if key not in _TRAJ:
        z = _traj_batch(surf)
        d = data()[surf]
        j = int(np.searchsorted(z["sel"], idx))
        assert z["sel"][j] == idx
        _TRAJ[key] = dict(ht=z["ht"], hs=z["hs"][:, j], hth=z["hth"][:, j],
                          t_off=float(z["t_off"][j]), th=float(z["th"][j]), w=float(z["w"][j]),
                          x=float(z["x"][j]), y=float(z["y"][j]), vx=float(z["vx"][j]), vy=float(z["vy"][j]),
                          t_land=float(z["t_land"][j]), rot=float(z["rot"][j]), a=float(d["a"][idx]), b=float(d["b"][idx]),
                          h=float(d["h"][idx]), v0=float(d["v0"][idx]), down=bool(butter_down(z["rot"][j:j + 1])[0]))
    return _TRAJ[key]


def pose(tr, u):
    """角を越えてから u 秒後の重心 (x, y)（m、角が原点・上が正）と傾き th、着地の済み具合"""
    if u < 0:
        return tr["v0"] * u, 0.0, 0.0, 0.0
    if u < tr["t_off"]:
        s = float(np.interp(u, tr["ht"], tr["hs"]))
        th = float(np.interp(u, tr["ht"], tr["hth"]))
        return s * math.cos(th), -s * math.sin(th), th, 0.0
    v = min(u - tr["t_off"], tr["t_land"])
    x = tr["x"] + tr["vx"] * v
    y = tr["y"] + tr["vy"] * v - 0.5 * G * v * v
    th = tr["th"] + tr["w"] * v
    settle = clamp01((u - tr["t_off"] - tr["t_land"]) / 0.12) if u - tr["t_off"] > tr["t_land"] else 0.0
    return x, y, th, settle


def flat_angle(rot, down):
    """着地のあと、板が寝る向き（いちばん近い 0°/180° の倍数のうち、上下が合うもの）"""
    k = round((rot - (math.pi if down else 0.0)) / (2 * math.pi))
    return (math.pi if down else 0.0) + 2 * math.pi * k


# ---------- 時間割（表示の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
SLOW = 3.0                                        # 見本はゆっくり（世界の1秒＝動画の3秒）
T_PUSH = T_GO + 0.15                              # 手がトーストを押しはじめる
PUSH_DUR = 0.8
T_S0 = T_PUSH + PUSH_DUR                          # 見本の重心が角を越える
T_SDONE = T_S0 + 2.45                             # 見本が2枚とも着地して札が出るころ
T_D0 = T_SDONE + 1.0                              # 1万枚ずつ
D_DUR = 5.0
T_D1 = T_D0 + D_DUR
T_FL = T_D1 + 0.2                                 # 数字が出そろう
T_REV = T_FL + 0.7                                # 三択の答え
T_ST2 = T_REV + 0.3                               # 付箋「テーブルなら98%」
T_H0 = T_ST2 + 2.7                                # 驚き: 回った角度のヒストグラム
H_DUR = 4.8
T_TW = T_H0 + H_DUR                               # ひねり: 高い棚
TW_BANNER = 2.8
T_TW_RUN = T_TW + TW_BANNER
TW_DUR = 1.6
T_VAL = T_TW_RUN + TW_DUR + 0.1
T_Q = T_VAL + 3.2                                 # 締め
DURATION = T_Q + 3.9

BIG_Q = "バターの面が下になるのは、気のせい？"
DETAIL = "トーストをそっと落とす。1万枚でためす"            # 2026-10-11 ユーザー案1（棚からも落とすので「テーブルから」を外す）
LABELS = ["気のせい", "7割くらい", "9割以上"]
CORRECT = 2

# ---------- 色 ----------
CRUST, CRUMB, CRUMB_B = "#a8622b", "#e8b672", "#dda564"
BUTTER, BUTTER_D = "#ffd84d", "#d9a400"
DOWN_COL, UP_COL = "#e2595f", "#ffd84d"           # マス目: バターが下＝赤（ベチャッ）／上＝黄
WOOD, WOOD_D = "#d8b07c", "#b98a52"
SKIN = "#ffe9cf"
SHELF_COL = "#c9d9c0"
GRN = "#2f8f5b"
KX, KY = 0.42, 0.30                               # トーストの面を斜め上から見る向き


# ---------- 絵: トースト ----------
def draw_toast(ctx, cx, cy, th, L, a=1.0, mirror=False, thick=None):
    """回るトースト（横から見た板を、斜め上から少しのぞく）。th は外側が下がる向きが正（0＝バターが上）。
    見えている面がバターの面なら、黄色いバターを描く"""
    if a <= 0:
        return
    sx = -1.0 if mirror else 1.0
    ex, ey = sx * math.cos(th), math.sin(th)                    # 板に沿う向き（画面の下が正）
    ntx, nty = sx * math.sin(th), -math.cos(th)                 # バターの面の向き（画面）
    top_vis = (ntx * KX + (-nty) * KY) > 0
    nvx, nvy = (ntx, nty) if top_vis else (-ntx, -nty)
    hl = L / 2
    dx, dy = KX * hl * 0.9, -KY * hl * 0.9                      # 奥行き
    tk = thick if thick is not None else max(4.0, L * 0.16)

    def quad(ox, oy, k=1.0):
        return [(ox + sgn1 * ex * hl * k + sgn2 * dx * k, oy + sgn1 * ey * hl * k + sgn2 * dy * k)
                for sgn1, sgn2 in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    if a < 1:
        ctx.push_group()
    # 耳（厚み）: 奥の面を少しずらして塗る
    back = quad(cx - nvx * tk / 2, cy - nvy * tk / 2)
    front = quad(cx + nvx * tk / 2, cy + nvy * tk / 2)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for i in range(4):
        p0, p1 = front[i], front[(i + 1) % 4]
        q0, q1 = back[i], back[(i + 1) % 4]
        ctx.move_to(*p0)
        ctx.line_to(*p1)
        ctx.line_to(*q1)
        ctx.line_to(*q0)
        ctx.close_path()
        fill(ctx, CRUST)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(2.2)
        ctx.stroke()
    # 見えている面
    ctx.move_to(*front[0])
    for p in front[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    fill(ctx, CRUMB if top_vis else CRUMB_B)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(CRUST))
    ctx.set_line_width(max(3.0, L * 0.07))
    ctx.stroke_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(2.2)
    ctx.stroke()
    if top_vis:
        fx, fy = cx + nvx * tk / 2, cy + nvy * tk / 2
        pat = quad(fx, fy, 0.48)
        ctx.move_to(*pat[0])
        for p in pat[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        fill(ctx, BUTTER)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(BUTTER_D))
        ctx.set_line_width(2.0)
        ctx.stroke()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def draw_splat(ctx, cx, cy, L, a=1.0):
    """バターが下で着地したとき、下からはみ出したバター"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(1.0, 0.28)
    fill(ctx, hexrgb(BUTTER, 0.9 * a))
    ctx.arc(0, 0, L * 0.62, 0, 2 * math.pi)
    ctx.fill()
    ctx.restore()


def draw_hand(ctx, x, y, a=1.0, mirror=False, s=1.0):
    """右向きに押す手（ペン描き）。(x, y) は指先の下"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(-s if mirror else s, s)
    if a < 1:
        ctx.push_group()
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    # そで
    core.rrect(ctx, -118, -40, 52, 40, 8)
    fill(ctx, "#a9d0f2")
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(3.5)
    ctx.stroke()
    # 手のひら（指をそろえて押す）
    ctx.move_to(-68, -36)
    ctx.curve_to(-40, -44, -10, -34, -2, -22)
    ctx.curve_to(4, -12, 2, -2, -6, 0)
    ctx.line_to(-68, 0)
    ctx.close_path()
    fill(ctx, SKIN)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.stroke()
    for yy in (-24, -12):
        ctx.move_to(-30, yy)
        ctx.line_to(-6, yy + 1)
        ctx.set_line_width(2)
        ctx.stroke()
    # 親指
    ctx.move_to(-56, -36)
    ctx.curve_to(-46, -54, -26, -52, -24, -40)
    ctx.set_line_width(3.5)
    ctx.stroke()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


def ink_line(ctx, x0, y0, x1, y1, color=INK, seed=1, width=3.5, alpha=1.0):
    """ペンの線（note.pen_line より揺れを小さく。家具の輪郭・床・マス目の枠が曲がって見えないように）"""
    if alpha <= 0:
        return
    rng = np.random.default_rng(seed)
    b = rng.uniform(-1.6, 1.6)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(color, 0.92 * alpha))
    L = math.hypot(x1 - x0, y1 - y0) or 1.0
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    ctx.move_to(x0, y0)
    ctx.curve_to(x0 + (x1 - x0) / 3 + nx * b, y0 + (y1 - y0) / 3 + ny * b,
                 x0 + 2 * (x1 - x0) / 3 - nx * b * 0.6, y0 + 2 * (y1 - y0) / 3 - ny * b * 0.6, x1, y1)
    ctx.stroke()


def draw_table(ctx, x0, x1, ytop, yfloor, a=1.0, seed=1, legs=True):
    if a <= 0:
        return
    th = 16
    ctx.set_source_rgba(*hexrgb(WOOD, a))
    ctx.rectangle(x0, ytop, x1 - x0, th)
    ctx.fill()
    for (xa, ya, xb, yb, sd) in ((x0, ytop, x1, ytop, seed), (x1, ytop, x1, ytop + th, seed + 1),
                                 (x1, ytop + th, x0, ytop + th, seed + 2), (x0, ytop + th, x0, ytop, seed + 3)):
        ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3.5, alpha=a)
    if legs:
        for lx in (x0 + 22, x1 - 34):
            ctx.set_source_rgba(*hexrgb(WOOD_D, a))
            ctx.rectangle(lx, ytop + th, 12, yfloor - ytop - th)
            ctx.fill()
            ink_line(ctx, lx, ytop + th, lx, yfloor, INK, seed=seed + 5, width=3, alpha=a)
            ink_line(ctx, lx + 12, ytop + th, lx + 12, yfloor, INK, seed=seed + 6, width=3, alpha=a)


def draw_shelf(ctx, x0, x1, ytop, yfloor, a=1.0):
    if a <= 0:
        return
    ctx.set_source_rgba(*hexrgb(SHELF_COL, a))
    ctx.rectangle(x0, ytop, x1 - x0, yfloor - ytop)
    ctx.fill()
    for (xa, ya, xb, yb, sd) in ((x0, ytop, x1, ytop, 21), (x1, ytop, x1, yfloor, 22),
                                 (x1, yfloor, x0, yfloor, 23), (x0, yfloor, x0, ytop, 24)):
        ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3.5, alpha=a)
    n_sh = 4
    rng = np.random.default_rng(9)
    for k in range(1, n_sh + 1):
        yy = ytop + (yfloor - ytop) * k / (n_sh + 1)
        ink_line(ctx, x0 + 6, yy, x1 - 6, yy, INK, seed=30 + k, width=3, alpha=0.8 * a)
        # 本（色の四角を数冊）
        xx = x0 + 16
        while xx < x1 - 40 and k < n_sh + 1:
            w = rng.uniform(14, 24)
            hh = rng.uniform(40, 62)
            if rng.random() < 0.8:
                col = ("#9fb8e8", "#f2b8a0", "#bfe0a0", "#f3e3a0", "#d7b8e8")[rng.integers(0, 5)]
                ctx.set_source_rgba(*hexrgb(col, 0.9 * a))
                ctx.rectangle(xx, yy - hh, w, hh)
                ctx.fill()
                ctx.set_source_rgba(*hexrgb(INK, 0.6 * a))
                ctx.set_line_width(2)
                ctx.rectangle(xx, yy - hh, w, hh)
                ctx.stroke()
            xx += w + rng.uniform(2, 8)


# ---------- 冒頭の絵: 高さのちがう3つの家具から、0秒目に次々と落ちる ----------
# 2026-10-11 v3（ユーザー「2このマスがよくわからない。落とす高さを変えているんだから、冒頭もいろんな高さで」）:
# 冒頭の空のマス目をやめ、低いテーブル（75cm）・カウンター（1m）・高い棚（1.8m）を床に並べる。
# v4（ユーザー「真ん中の棚が上の文字と被り気味だからもう少し下げて。後トーストは床まで落として」）:
# 家具の絵ぜんたいを少し縮めて棚の天板を三択の下へ。トーストは床まで落とし、0.4秒置いてから消す。
# 着地の向きは1万枚と同じ計算（テーブル・棚はそれぞれの1万枚の値。カウンターはテーブルの1万枚の端の動きを高さ1mで落とす）
D_FLOOR = 1440.0                                  # 冒頭の床（字は置かない）
D_SCALE = 405.0                                   # 1m あたりの px（棚 1.8m の天板が y≈711）
# (左端, 右端, 高さ m, 種類, 使う1万枚)
D_FURN = [(108.0, 318.0, 0.75, "table", "table"),
          (472.0, 632.0, 1.80, "shelf", "shelf"),
          (792.0, 982.0, 1.00, "counter", "table")]
D_PERIOD = 0.21
D_SLIDE = 0.30                                    # 天板の真ん中寄りから角まですべる時間（動画の秒）
D_SPEED = 1.0                                     # 冒頭も実際の速さ
D_LEN = 74.0                                      # 描くトーストの長さ（px。実物の約1.7倍）
D_REST, D_OUT = 0.4, 0.3                          # 床に着いてから置いておく秒・消える秒
CD_X, CD_Y = 860.0, 875.0                         # 予想して！のカウント（カウンターの上の空き）


def d_top(i):
    return D_FLOOR - D_FURN[i][2] * D_SCALE


def deco_jobs():
    """冒頭で落ちるトースト: (家具の番号, 右端か, 出る時刻, 見本の番号)"""
    jobs = []
    # 1万枚のうちの160枚（統計に使う1万枚と同じ値。端の上の動きは高さによらない）
    pool = np.arange(40, 200)
    k = 0
    for i in range(len(D_FURN)):
        per = D_PERIOD * (0.8 if D_FURN[i][3] == "shelf" else 1.0)
        for side in (0, 1):
            ph = (i * 0.29 + side * 0.17) % per
            t0 = -1.6 + ph
            while t0 < T_GO + 0.5:
                jobs.append((i, side == 1, t0, int(pool[(k * 7) % len(pool)])))
                t0 += per * (1 + 0.3 * math.sin(k * 1.7 + i))
                k += 1
    return jobs


DECO = None


def draw_counter(ctx, x0, x1, ytop, yfloor, a=1.0):
    """台所のカウンター（天板＋戸棚）"""
    if a <= 0:
        return
    th = 18
    ctx.set_source_rgba(*hexrgb("#e8dcc4", a))
    ctx.rectangle(x0 + 8, ytop + th, x1 - x0 - 16, yfloor - ytop - th)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(WOOD, a))
    ctx.rectangle(x0, ytop, x1 - x0, th)
    ctx.fill()
    for (xa, ya, xb, yb, sd) in ((x0, ytop, x1, ytop, 41), (x1, ytop, x1, ytop + th, 42),
                                 (x1, ytop + th, x0, ytop + th, 43), (x0, ytop + th, x0, ytop, 44),
                                 (x0 + 8, ytop + th, x0 + 8, yfloor, 45), (x1 - 8, ytop + th, x1 - 8, yfloor, 46)):
        ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3.5, alpha=a)
    xm = (x0 + x1) / 2
    ink_line(ctx, xm, ytop + th + 10, xm, yfloor - 14, INK, seed=47, width=3, alpha=0.8 * a)
    ink_line(ctx, x0 + 18, ytop + th + 62, x1 - 18, ytop + th + 62, INK, seed=48, width=3, alpha=0.8 * a)
    for hxp in (xm - 16, xm + 16):                 # 取っ手
        ink_line(ctx, hxp, ytop + th + 100, hxp, ytop + th + 136, INK, seed=49, width=4, alpha=0.8 * a)


def draw_deco(ctx, t, a):
    global DECO
    if a <= 0:
        return
    if DECO is None:
        DECO = deco_jobs()
    ink_line(ctx, 58, D_FLOOR + 2, 1022, D_FLOOR + 1, INK, seed=4, width=4.5, alpha=0.8 * a)
    for i, (x0, x1, hm, kind, _src) in enumerate(D_FURN):
        top = d_top(i)
        if kind == "table":
            draw_table(ctx, x0, x1, top, D_FLOOR, a=a, seed=3)
        elif kind == "shelf":
            draw_shelf(ctx, x0, x1, top, D_FLOOR, a=a)
        else:
            draw_counter(ctx, x0, x1, top, D_FLOOR, a=a)
    for (i, right, t0, idx) in DECO:
        u_v = t - t0
        if u_v < 0:
            continue
        tr = deco_traj(i, idx)
        t_end = D_SLIDE + (tr["t_off"] + tr["t_land"]) / D_SPEED
        if u_v > t_end + D_REST + D_OUT:
            continue
        x0, x1, hm, kind, _src = D_FURN[i]
        top = d_top(i)
        edge = x1 if right else x0
        sgn = 1.0 if right else -1.0
        fa = 1 - clamp01((u_v - t_end - D_REST) / D_OUT)
        if u_v < D_SLIDE:                         # 天板の上をすべって角へ
            p = ease_out(u_v / D_SLIDE)
            xm = -((x1 - x0) / 2 * 0.5 / D_SCALE) * (1 - p)
            cx = edge + sgn * xm * D_SCALE
            cy = top - 7
            th = 0.0
        else:
            u = (u_v - D_SLIDE) * D_SPEED
            xm, ym, th, settle = pose(tr, u)
            cx = edge + sgn * xm * D_SCALE
            cy = top - 7 - ym * D_SCALE
            if settle > 0:                        # 着地したら、計算どおりの面を下にして寝かせる
                th = th + (flat_angle(tr["rot"], tr["down"]) - th) * ease(settle)
            lowest = cy + (D_LEN / 2) * abs(math.sin(th)) + 6 * abs(math.cos(th))
            if lowest > D_FLOOR - 1:              # 描くトーストは実物より大きいので、床にめり込ませない
                cy -= lowest - (D_FLOOR - 1)
            if tr["down"] and u_v >= t_end:
                draw_splat(ctx, cx, D_FLOOR - 1, D_LEN, a=a * fa * ease_out((u_v - t_end) / 0.12))
        draw_toast(ctx, cx, cy, th, D_LEN, a=a * fa, mirror=not right)


_DTRAJ = {}


def deco_traj(i, idx):
    """冒頭の1枚の動き。端の上の動きは1万枚と同じ値。着地はその家具の高さで計算する"""
    key = (i, idx)
    if key not in _DTRAJ:
        x0, x1, hm, kind, src = D_FURN[i]
        tr = dict(traj(src, idx))
        if kind == "counter":                     # テーブルの1万枚の1枚を、高さ1m（±4cm、テーブルと同じばらつき）から
            h = tr["h"] - 0.75 + hm
            o = dict(th=np.array([tr["th"]]), thd=np.array([tr["w"]]), y=np.array([tr["y"]]), vy=np.array([tr["vy"]]))
            tl, rot = landing(o, np.array([tr["a"]]), np.array([tr["b"]]), np.array([h]))
            tr.update(t_land=float(tl[0]), rot=float(rot[0]), down=bool(butter_down(rot)[0]), h=h)
        _DTRAJ[key] = tr
    return _DTRAJ[key]


def deco_down_share(t_max=None):
    """冒頭（カウントが終わるまで）に床に着く枚数と、そのうちバターが下の枚数（家具ごと）"""
    t_max = T_MOVE if t_max is None else t_max
    out = {}
    for (i, right, t0, idx) in deco_jobs():
        tr = deco_traj(i, idx)
        tl = t0 + D_SLIDE + (tr["t_off"] + tr["t_land"]) / D_SPEED
        if 0 <= tl < t_max:
            n, d = out.get(D_FURN[i][3], (0, 0))
            out[D_FURN[i][3]] = (n + 1, d + int(tr["down"]))
    return out


# ---------- シミュの舞台（本体の座標。draw 側で translate(PAGE_DX)） ----------
FLOOR = 1010.0
S_SCALE = 220.0                                   # 1m あたりの px
TOP_Y = {"table": FLOOR - 0.75 * S_SCALE, "shelf": FLOOR - 1.8 * S_SCALE}
EDGE_X = {"table": 300.0, "shelf": 655.0}
SURF_X0 = {"table": 75.0, "shelf": 455.0}
S_LEN = 54.0                                      # 描くトーストの長さ（実物の約2倍。見やすさのため）
GRID_X = {"table": 95.0, "shelf": 525.0}          # マス目の左端
GRID_Y, GRID_PX = 1075.0, 260.0
GRID_N = 100                                      # 100×100＝1万マス
CAP_Y = 1366.0
NAME = {"table": "テーブル\n75cm", "shelf": "高い棚\n1.8m"}


def stage_alpha(t):
    """舞台（机・棚・床・手）の見え方。冒頭が終わるときに出て、ヒストグラムの前に消える"""
    if t < T_MOVE:
        return 0.0
    if t < T_H0:
        return ease((t - T_MOVE) / 0.4)
    return 1 - ease((t - T_H0) / 0.3)


def grid_alpha(t):
    if t < T_H0:
        return ease((t - T_MOVE) / 0.4)
    return 1 - ease((t - T_H0) / 0.3)


def toast_screen(surf, tr, u):
    """角を越えてから u 秒後のトーストの画面上の (x, y, th)。描く板が実物より大きいので、床にめり込まないようにする"""
    xm, ym, th, settle = pose(tr, u)
    cx = EDGE_X[surf] + xm * S_SCALE
    cy = TOP_Y[surf] - 6 - ym * S_SCALE
    if settle > 0:
        th_f = flat_angle(tr["rot"], tr["down"])
        th = th + (th_f - th) * ease(settle)
    lowest = cy + (S_LEN / 2) * abs(math.sin(th)) + 5 * abs(math.cos(th))
    if lowest > FLOOR - 1:
        cy -= lowest - (FLOOR - 1)
    return cx, cy, th


def draw_stage(ctx, t, a):
    if a <= 0:
        return
    ink_line(ctx, 50, FLOOR + 2, 890, FLOOR + 1, INK, seed=4, width=4.5, alpha=0.8 * a)
    draw_table(ctx, SURF_X0["table"], EDGE_X["table"], TOP_Y["table"], FLOOR, a=a, seed=11)
    draw_shelf(ctx, SURF_X0["shelf"], EDGE_X["shelf"], TOP_Y["shelf"], FLOOR, a=a)
    text(ctx, NAME["table"], (SURF_X0["table"] + EDGE_X["table"]) / 2 - 5, TOP_Y["table"] + 72, 30, INK, alpha=a)
    text(ctx, NAME["shelf"], SURF_X0["shelf"] - 62, TOP_Y["shelf"] + 50, 30, INK, alpha=a)


def draw_samples(ctx, t, a):
    """見本: 手でそっと押した1枚ずつ（ゆっくり）"""
    if a <= 0 or t < T_GO:
        return
    out = 1 - ease((t - (T_D0 + 0.6)) / 0.4) if t > T_D0 + 0.6 else 1.0
    for surf in ("table", "shelf"):
        tr = traj(surf, typical(surf))
        y = TOP_Y[surf] - 6
        # 手: 押してから少し引く
        if t < T_S0:
            p = ease(clamp01((t - T_PUSH) / PUSH_DUR))
            cx = EDGE_X[surf] - 0.11 * S_SCALE * (1 - p) - 4 * (1 - p)
            hx = cx - S_LEN / 2 - 2
        else:
            u = (t - T_S0) / SLOW
            cx, cy, th = toast_screen(surf, tr, u)
            hx = EDGE_X[surf] - S_LEN / 2 - 2 - 40 * ease(clamp01((t - T_S0) / 0.6))
        ha = a * ease_out((t - T_GO) / 0.3) * (1 - ease((t - T_D0) / 0.4))
        draw_hand(ctx, hx, y + 8, a=ha, s=0.62)
        if t < T_S0:
            draw_toast(ctx, cx, y, 0.0, S_LEN, a=a * out * ease_out((t - T_GO) / 0.3))
            continue
        land_v = T_S0 + SLOW * (tr["t_off"] + tr["t_land"])
        if tr["down"] and t >= land_v:
            draw_splat(ctx, cx, FLOOR - 1, S_LEN, a=a * out * ease_out((t - land_v) / 0.15))
        draw_toast(ctx, cx, cy, th, S_LEN, a=a * out)
        if t >= land_v + 0.15:
            b = ease_out((t - land_v - 0.15) / 0.25) * a * out
            lab = "バターが下" if tr["down"] else "バターが上"
            note.sticky(ctx, lab, cx + (45 if surf == "table" else 40), FLOOR - 96, 30, "pink" if tr["down"] else "yellow",
                        fg=RED if tr["down"] else INK, a=b, tilt=-0.03)


FAST_K = 46                                       # 1万枚の場面で、絵として落とす枚数（1つの台につき）
FAST_SPAN = D_DUR - 0.9


def draw_fast(ctx, t, a):
    """1万枚の場面: 次々と落ちる（絵は代表の数十枚。数はマス目とカウンターが1万枚ぶん数える）"""
    if a <= 0 or t < T_D0 - 0.1 or t > T_FL + 1.2:
        return
    for surf in ("table", "shelf"):
        y = TOP_Y[surf] - 6
        for j in range(FAST_K):
            t0 = T_D0 + j * FAST_SPAN / FAST_K + (0.05 if surf == "shelf" else 0.0)
            u_v = t - t0
            if u_v < 0:
                continue
            tr = traj(surf, j)
            tl = tr["t_off"] + tr["t_land"]
            if u_v > 0.12 + tl + 0.7:
                continue
            fa = 1 - clamp01((u_v - 0.12 - tl - 0.35) / 0.35)
            if u_v < 0.12:
                p = ease_out(u_v / 0.12)
                cx = EDGE_X[surf] - 0.10 * S_SCALE * (1 - p)
                cy, th = y, 0.0
            else:
                cx, cy, th = toast_screen(surf, tr, u_v - 0.12)
                if tr["down"] and u_v - 0.12 >= tl:
                    draw_splat(ctx, cx, FLOOR - 1, S_LEN, a=a * fa)
            draw_toast(ctx, cx, cy, th, S_LEN, a=a * fa)


def counts_at(t):
    """1万枚の場面の、落とし終えた枚数（テーブルと棚で同じ）"""
    if t < T_D0:
        return 0
    return int(N_SLICE * clamp01((t - T_D0) / D_DUR) ** 1.15)


_ORDER = {}


def grid_colors(surf, k):
    """落とし終えた k 枚ぶんを塗ったマス目。バターが下（赤）は左上から、上（黄）は右下から埋める"""
    d = data()[surf]
    dn = butter_down(d["rot"][:k])
    nd = int(dn.sum())
    nu = k - nd
    c = np.zeros((GRID_N * GRID_N, 4), np.uint8)
    if nd:
        c[:nd] = _bgra(DOWN_COL)
    if nu:
        c[GRID_N * GRID_N - nu:] = _bgra(UP_COL)
    return c.reshape(GRID_N, GRID_N, 4), nd


def _bgra(col):
    r = hexrgb(col)
    return np.array([int(r[2] * 255), int(r[1] * 255), int(r[0] * 255), 255], np.uint8)


def draw_grids(ctx, t, a, intro=False):
    """1万枚のマス目2つ（冒頭は空のまま）と、その下のカウンター"""
    if a <= 0:
        return
    k = 0 if intro else counts_at(t)
    for surf in ("table", "shelf"):
        gx = GRID_X[surf]
        if k > 0:
            cols, nd = grid_colors(surf, k)
            cols = np.ascontiguousarray(cols)
            surf_img = cairo.ImageSurface.create_for_data(memoryview(cols), cairo.FORMAT_ARGB32, GRID_N, GRID_N, GRID_N * 4)
            ctx.save()
            ctx.translate(gx, GRID_Y)
            ctx.scale(GRID_PX / GRID_N, GRID_PX / GRID_N)
            ctx.set_source_surface(surf_img, 0, 0)
            ctx.get_source().set_filter(cairo.FILTER_NEAREST)
            ctx.paint_with_alpha(a)
            ctx.restore()
        else:
            nd = 0
        # 枠（鉛筆）と方眼の目安
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
        ctx.set_line_width(1.2)
        for q in range(1, 10):
            v = GRID_PX * q / 10
            ctx.move_to(gx + v, GRID_Y)
            ctx.line_to(gx + v, GRID_Y + GRID_PX)
            ctx.move_to(gx, GRID_Y + v)
            ctx.line_to(gx + GRID_PX, GRID_Y + v)
        ctx.stroke()
        for (xa, ya, xb, yb, sd) in ((gx, GRID_Y, gx + GRID_PX, GRID_Y, 71), (gx + GRID_PX, GRID_Y, gx + GRID_PX, GRID_Y + GRID_PX, 72),
                                     (gx + GRID_PX, GRID_Y + GRID_PX, gx, GRID_Y + GRID_PX, 73), (gx, GRID_Y + GRID_PX, gx, GRID_Y, 74)):
            ink_line(ctx, xa, ya, xb, yb, INK, seed=sd, width=3.5, alpha=0.85 * a)
        cx = gx + GRID_PX / 2
        if intro or k == 0:
            text(ctx, "テーブル" if surf == "table" else "高い棚", cx, GRID_Y + GRID_PX / 2, 38, PENCIL, bold=False, alpha=0.8 * a)
            text(ctx, "1万枚", cx, GRID_Y + GRID_PX / 2 + 50, 30, PENCIL, bold=False, alpha=0.8 * a)
        col = RED if (k > 0 and t >= T_FL and surf == "table") else INK
        text(ctx, f"バターが下 {nd:,}枚", cx, CAP_Y, 34, col, alpha=a)
        text(ctx, "/ 10,000枚", cx, CAP_Y + 44, 28, PENCIL, bold=False, alpha=a)


def legend_row(ctx, a):
    if a <= 0:
        return
    note.legend(ctx, [(DOWN_COL, "バターが下"), (UP_COL, "バターが上")], FLOOR + 38, 28, gap=50)


# ---------- 驚き・ひねり: 床に着くまでに回った角度 ----------
HX0, HX1, HY0, HY1 = 150.0, 815.0, 840.0, 1190.0
DEG_MAX = 540.0
BIN = 10.0


def hx(deg):
    return HX0 + deg / DEG_MAX * (HX1 - HX0)


_HIST = {}


def hist(surf):
    if surf not in _HIST:
        deg = np.degrees(data()[surf]["rot"])
        edges = np.arange(0, DEG_MAX + BIN, BIN)
        cnt, _ = np.histogram(np.clip(deg, 0, DEG_MAX - 1e-6), edges)
        _HIST[surf] = (edges, cnt)
    return _HIST[surf]


HIST_YMAX = None


def draw_hist(ctx, surf, grow, a, ghost=False):
    global HIST_YMAX
    if a <= 0 or grow <= 0:
        return
    if HIST_YMAX is None:
        HIST_YMAX = max(hist("table")[1].max(), hist("shelf")[1].max()) * 1.08
    edges, cnt = hist(surf)
    for i in range(len(cnt)):
        if cnt[i] == 0:
            continue
        mid = (edges[i] + edges[i + 1]) / 2
        dn = butter_down(np.array([math.radians(mid)]))[0]
        h = cnt[i] / HIST_YMAX * (HY1 - HY0) * grow
        x0, x1 = hx(edges[i]) + 1, hx(edges[i + 1]) - 1
        if ghost:
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * a))
        else:
            ctx.set_source_rgba(*hexrgb(DOWN_COL if dn else UP_COL, 0.9 * a))
        ctx.rectangle(x0, HY1 - h, x1 - x0, h)
        ctx.fill()
        if not ghost:
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
            ctx.set_line_width(1.6)
            ctx.rectangle(x0, HY1 - h, x1 - x0, h)
            ctx.stroke()


def draw_hist_axes(ctx, a):
    if a <= 0:
        return
    # バターが下の帯（90〜270°、450〜540°）
    for lo, hi in ((90, 270), (450, 540)):
        ctx.set_source_rgba(*hexrgb(DOWN_COL, 0.10 * a))
        ctx.rectangle(hx(lo), HY0 - 20, hx(hi) - hx(lo), HY1 - HY0 + 20)
        ctx.fill()
    for deg in (90, 270, 450):
        ctx.set_source_rgba(*hexrgb(RED, 0.6 * a))
        ctx.set_line_width(2.5)
        ctx.set_dash([8, 7])
        ctx.move_to(hx(deg), HY0 - 20)
        ctx.line_to(hx(deg), HY1)
        ctx.stroke()
        ctx.set_dash([])
    text(ctx, "バターが下", hx(180), HY0 - 45, 32, RED, alpha=a)
    text(ctx, "バターが上", hx(360), HY0 - 45, 32, "#a07800", alpha=a)
    note.pen_line(ctx, HX0 - 6, HY1 + 3, HX1 + 8, HY1 + 3, INK, seed=4, width=4.5, alpha=0.85 * a)
    for deg in (0, 180, 360, 540):
        xx = hx(deg)
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, HY1 + 3)
        ctx.line_to(xx, HY1 + 13)
        ctx.stroke()
    for deg, lab in ((0, "0"), (180, "半回転"), (360, "1回転"), (540, "1回転半")):
        text(ctx, lab, hx(deg), HY1 + 40, 28, INK, bold=False, alpha=a)
        # 向きの小さなトースト
        draw_toast(ctx, hx(deg), HY1 + 92, math.radians(deg), 46, a=a)
    text(ctx, "床に着くまでに回った角度", (HX0 + HX1) / 2, HY1 + 146, 30, INK, bold=False, alpha=a)


def number_row(ctx, parts, y, a, size=44, cx=470):
    ws = [core.text_width(s, size) for s, _ in parts]
    x = cx - sum(ws) / 2
    for (s, col), w in zip(parts, ws):
        text(ctx, s, x, y, size, col, align="left", alpha=a)
        x += w


# ---------- 冒頭・上のブロック ----------

class TIntro(note.Intro):
    """この回だけの冒頭。上: 問いの1行・前提・三択（横1列）。その下の画面いっぱいに、
    高さのちがう家具（テーブル・高い棚・カウンター）から0秒目からトーストが次々と落ちる（床のずっと上で消える）。
    予想して！とカウントはカウンターの上の空き"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        draw_deco(ctx, t, a)
        sz = 62
        w = core.text_width(BIG_Q, sz)
        if w > 800:
            sz *= 800 / w
            w = 800
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))       # 0秒目から読める大きさで、ポンと置く
        ctx.save()
        ctx.translate(575, 418)
        ctx.scale(pop, pop)
        text(ctx, BIG_Q, 0, 0, sz, INK, alpha=a)
        ctx.restore()
        note.pen_line(ctx, 575 - w / 2 - 6, 462, 575 + w / 2 + 6, 456, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 500, 36, INK, bold=False, alpha=a1)
        for i, v in enumerate(self.labels):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            cx = 580 + (i - 1) * 310
            vs = 42
            vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2 + 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 566, 28, 28, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 566, 38, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 64, 566, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            note.hand_text(ctx, "予想して！", cx, cy - 138, 46, RED, seed=41, alpha=a2, align="center")
            fill(ctx, (*hexrgb(PAPER)[:3], 0.92 * a))
            ctx.arc(cx, cy, 70, 0, 2 * math.pi)
            ctx.fill()
            note.pen_circle(ctx, cx, cy, 66, 64, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 96, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
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
            al = m * (1 - 0.55 * rev * (not ok))
            vs = 44
            vw = core.text_width(v, vs)
            if 64 + vw > 252:
                vs *= (252 - 64) / vw
                vw = core.text_width(v, vs)
            x0 = cx - (64 + vw) / 2
            note.pen_circle(ctx, x0 + 27, y, 27, 27, INK, seed=i + 7, width=4, alpha=al)
            text(ctx, "ABC"[i], x0 + 27, y, 36, INK, alpha=al)
            text(ctx, v, x0 + 64, y, vs, RED if (ok and rev > 0.5) else INK, align="left", alpha=al)
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


INTRO = TIntro(["バターの面が下になるのは、", "気のせい？"], LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    sh = shown()
    sa = stage_alpha(t)
    draw_stage(ctx, t, sa)
    legend_row(ctx, sa)
    draw_samples(ctx, t, sa)
    draw_fast(ctx, t, sa)
    if T_D0 - 0.6 <= t < T_D0 + 1.2:
        b = ease_out((t - T_D0 + 0.6) / 0.3) * (1 - ease((t - T_D0 - 0.8) / 0.4))
        text(ctx, "1万枚ずつ落とす", 195, 720, 36, INK, alpha=b)
    # 答え
    if T_ST2 <= t < T_H0 + 0.3:
        b = ease_out((t - T_ST2) / 0.3) * (1 - ease((t - T_H0) / 0.3))
        note.sticky(ctx, f"テーブルなら\n{sh['table_pct']}%がバターが下", 255, 720, 40, "pink", fg=RED, a=b, tilt=-0.02)
    # 驚き: 回った角度
    ha = 0.0
    if t >= T_H0:
        ha = ease((t - T_H0 - 0.1) / 0.3)
        if t >= T_Q:
            ha *= 1 - 0.6 * ease_out((t - T_Q) / 0.35)
    if ha > 0:
        draw_hist_axes(ctx, ha)
        tw = t >= T_TW
        g_t = ease_out((t - T_H0 - 0.4) / 1.0)
        draw_hist(ctx, "table", g_t, ha, ghost=tw and t >= T_TW + 0.3)
        if not tw or t < T_TW + 0.3:
            k = 1 - (ease((t - T_TW) / 0.3) if tw else 0.0)
            if t >= T_H0 + 1.2:
                b = ease_out((t - T_H0 - 1.2) / 0.3) * ha * k
                number_row(ctx, [("テーブル（75cm） ", INK), ("ほぼ半回転", RED)], 1420, b, size=40)
            if t >= T_H0 + 1.6:
                b = ease_out((t - T_H0 - 1.6) / 0.3) * ha * k
                note.sticky(ctx, "床に着くまでに\nちょうど半回転", 470, 640, 44, "pink", fg=RED, a=b, tilt=-0.015)
        if tw:
            if t < T_TW_RUN:
                ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.2) / 0.2))
                note.banner(ctx, "高い棚だと、なぜ逆転？", 470, 650, a=ba, t_rel=t - T_TW, size=50)
            else:
                g2 = ease_out((t - T_TW_RUN) / TW_DUR)
                draw_hist(ctx, "shelf", g2, ha)
                b = ease_out((t - T_TW_RUN) / 0.3) * ha
                text(ctx, "テーブル", hx(sh["table_rot_med"]), HY1 - 30, 26, PENCIL, bold=False, alpha=0.9 * b)
                if t >= T_VAL:
                    b2 = ease_out((t - T_VAL) / 0.3) * ha
                    number_row(ctx, [("高い棚 バターが下 ", INK), (f"{sh['shelf_pct']}%", GRN)], 1420, b2, size=44)
                    if t < T_Q + 0.35:
                        note.sticky(ctx, "回りすぎて\nバターが上のほうが多い", 470, 640, 42, "mint",
                                    a=b2 * (1 - ease_out((t - T_Q) / 0.35)), tilt=-0.015)
    # 締め
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        note.sticky(ctx, "バターが重いから\n下になるの？", 470, 700, 52, "yellow", a=q, tilt=-0.02)
        if t >= T_Q + 1.8:
            text(ctx, "（トーストの「マーフィーの法則」）", 470, 1010, 32, PENCIL, bold=False, alpha=ease_out((t - T_Q - 1.8) / 0.3))
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, "答えは概要欄に", 470, 905, 50, "pink", fg=RED, a=r, tilt=0.025)


def scene(ctx, t):
    note.paper(ctx)
    INTRO.draw(ctx, t, reveal_t=T_REV)
    ctx.save()
    ctx.translate(note.PAGE_DX, 0)                  # 本体は紙の中心にそろえる（左はリングの穴）
    if t >= T_MOVE:                                  # マス目はシミュが始まるときに出す（冒頭には置かない）
        draw_grids(ctx, t, grid_alpha(t))
    body(ctx, t)
    ctx.restore()


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def soft_tap(freq=520.0, dur=0.09):
    """トーストが床に落ちる「ぱた」"""
    tt = _t(dur)
    n = np.random.default_rng(int(freq)).standard_normal(len(tt))
    n = np.convolve(n, np.ones(12) / 12, mode="same")
    return (n * 2.5 + 0.4 * np.sin(2 * np.pi * freq * tt)) * np.exp(-tt * 45)


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 293.7, 370.0)), 1.0, bgm=True)
    # 冒頭: トーストが角から離れるたびに小さな音
    for (i, right, t0, idx) in deco_jobs():
        tv = t0 + D_SLIDE
        if 0 <= tv < T_MOVE:
            mx.add(tv, tick(float(1500 + 300 * i + (200 if right else 0)), 0.03), 0.06)
    INTRO.audio(mx)
    # 見本
    mx.add(T_PUSH, whoosh(0.5), 0.12)
    for surf, f0 in (("table", 660.0), ("shelf", 520.0)):
        tr = traj(surf, typical(surf))
        land_v = T_S0 + SLOW * (tr["t_off"] + tr["t_land"])
        mx.add(land_v, soft_tap(f0), 0.5)
        mx.add(land_v + 0.15, blip(784.0 if tr["down"] else 1046.5, 0.2), 0.35)
    # 1万枚
    mx.add(T_D0 - 0.6, riser(0.8), 0.5)
    beat(mx, T_D0, T_D1, bpm=124, vol=0.5, accel=True)
    rng = np.random.default_rng(5)
    for j in range(FAST_K):
        for surf in ("table", "shelf"):
            tr = traj(surf, j)
            t0 = T_D0 + j * FAST_SPAN / FAST_K + (0.05 if surf == "shelf" else 0.0) + 0.12 + tr["t_off"] + tr["t_land"]
            mx.add(t0, soft_tap(float(rng.uniform(450, 750))), 0.12)
    mx.add(T_FL, thump(), 0.6)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ST2, blip(659.3, 0.15), 0.35)
    # 驚き
    mx.add(T_H0 + 0.4, riser(0.6), 0.3)
    mx.add(T_H0 + 1.6, bell(880.0, 1.0), 0.35)
    # ひねり
    mx.add(T_TW, riser(0.8), 0.45)
    beat(mx, T_TW_RUN, T_TW_RUN + TW_DUR, bpm=140, vol=0.45)
    mx.add(T_VAL, thump(), 0.6)
    mx.add(T_VAL + 0.1, bell(1046.5, 1.6), 0.5)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------
BACON_W = [(0.10, 6.93), (0.30, 8.80), (0.55, 10.03), (0.85, 10.90), (1.10, 11.57), (1.30, 12.2),
           (1.60, 12.47), (1.85, 12.57), (2.10, 12.17), (2.30, 12.43)]          # 表I（cm, rad/s）
BACON_UD = [(0.10, 1), (0.30, 1), (0.63, 1), (0.79, 1), (0.81, 0), (0.85, 0), (1.10, 0), (1.30, 0), (1.60, 0),
            (1.85, 0), (2.10, 0), (2.35, 0), (2.80, 0), (3.03, 1), (3.28, 1), (3.40, 1), (3.70, 1)]  # 表II（1＝下）


def bacon_check():
    a, b = 0.102 / 2, 0.013
    d0 = np.array([x for x, _ in BACON_W] + [x for x, _ in BACON_UD]) / 100
    n = len(d0)
    o = edge_phase(np.zeros(n), np.full(n, 0.32), np.full(n, 0.24), np.full(n, a), np.full(n, b), s0=d0)
    _, rot = landing(o, np.full(n, a), np.full(n, b), np.full(n, 0.76))
    nw = len(BACON_W)
    w_err = np.abs(o["thd"][:nw] - np.array([w for _, w in BACON_W])) / np.array([w for _, w in BACON_W])
    agree = (butter_down(rot[nw:]).astype(int) == np.array([u for _, u in BACON_UD])).mean()
    return float(w_err.mean()), float(agree), o["thd"][:nw], rot[nw:]


def run_checks():
    d = data()
    sh = shown()
    checks = []
    # (1) Bacon ら 2001 の実験
    w_err, agree, _, _ = bacon_check()
    checks.append(("Bacon ら(2001)表I: 回る速さのずれの平均（割合）", w_err, 0.0, 0.08))
    checks.append(("Bacon ら(2001)表II: 76cmからの上下が実験と一致する割合（17点）", agree, 1.0, 0.2))
    # (2) すべらない場合の閉じた式（薄い板）
    a = 0.05
    d0 = np.array([0.002, 0.005, 0.01, 0.02, 0.03])
    o = edge_phase(np.zeros(5), np.full(5, 1e9), np.full(5, 1e9), np.full(5, a), np.zeros(5), s0=d0)
    w2 = 6 * G * d0 * np.sin(o["th"]) / (a * a + 3 * d0 * d0)
    checks.append(("すべらない場合: ω² の相対誤差の最大（式14）", float(np.max(np.abs(o["thd"] ** 2 / w2 - 1))), 0.0, 0.01))
    # (3) 着地の判定 vs 二分法だけで解いた値（テーブルの最初の200枚）
    tb = d["table"]
    sel = slice(0, 200)
    oo = dict(th=tb["th_off"][sel], thd=tb["w"][sel], y=tb["y_off"][sel], vy=tb["vy"][sel])
    checks.append(("着地: 回った角度（度）の最大のずれ（刻み0.1ms＋二分法 vs 刻み0.01ms）",
                   float(np.degrees(np.max(np.abs(landing(oo, tb["a"][sel], tb["b"][sel], tb["h"][sel], dt=1e-5)[1] - tb["rot"][sel])))),
                   0.0, 0.05))
    # (4) 時間の刻みを半分にしても判定が変わらない（テーブル・棚の最初の400枚）
    for surf in ("table", "shelf"):
        dd = d[surf]
        sl = slice(0, 400)
        o2 = edge_phase(dd["v0"][sl], dd["mus"][sl], dd["muk"][sl], dd["a"][sl], dd["b"][sl], dt=DT / 2)
        _, rot2 = landing(o2, dd["a"][sl], dd["b"][sl], dd["h"][sl])
        same = (butter_down(rot2) == butter_down(dd["rot"][sl])).mean()
        checks.append((f"刻みを半分に（{surf}・400枚）: 上下の判定が同じ割合", float(same), 1.0, 0.01))
        checks.append((f"刻みを半分に（{surf}・400枚）: 回った角度のずれの平均（度）",
                       float(np.degrees(np.mean(np.abs(rot2 - dd["rot"][sl])))), 0.0, 1.0))
    # (5) 画面の % が、別の乱数の2万枚と同じ丸め
    for surf in ("table", "shelf"):
        checks.append((f"画面の%（{surf}）が別の乱数2万枚と同じ丸め", float(sh[surf + "_pct"]), float(pct(sh[surf + "_ref"])), 0.0))
        checks.append((f"画面の「バターが下 n枚」（{surf}）が1万枚の集計", float(sh[surf + "_n"]),
                       float(butter_down(d[surf]["rot"]).sum()), 0.0))
    # (6) 答え
    checks.append(("答えは C: テーブルで9割以上がバターが下", float(sh["table_p"] >= 0.90), 1.0, 0.0))
    checks.append(("A・B は外れ（7割台より上）", float(sh["table_p"] > 0.80), 1.0, 0.0))
    checks.append(("ひねり: 高い棚ではバターが下が半分を下回る", float(sh["shelf_p"] < 0.5), 1.0, 0.0))
    checks.append(("見本: テーブルはバターが下、棚はバターが上（それぞれ多いほう）",
                   float(traj("table", typical("table"))["down"] and not traj("shelf", typical("shelf"))["down"]), 1.0, 0.0))
    checks.append(("見本の記録し直しが1万枚の結果と同じ（テーブル）",
                   float(traj("table", typical("table"))["rot"]), float(d["table"]["rot"][typical("table")]), 1e-9))
    check_answers(checks)


if __name__ == "__main__" and "--compute" not in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    d = data()
    sh = shown()
    w_err, agree, wb, rb = bacon_check()
    print(f"長さ={DURATION:.1f}秒")
    for s in ("table", "shelf"):
        dd = d[s]
        print(f"{s}: バターが下 {sh[s + '_n']} / 10000 = {sh[s + '_p'] * 100:.2f}%（別の乱数2万枚 {sh[s + '_ref'] * 100:.2f}%）"
              f" 回った角度の中央値 {sh[s + '_rot_med']:.0f}° / すべった割合 {dd['slipped'].mean() * 100:.0f}%"
              f" / 回る速さの中央値 {np.median(dd['w']):.1f} rad/s / 見本 #{typical(s)}")
    print("Bacon 表I の再現:", " ".join(f"{x:.2f}" for x in wb), f"（ずれ平均 {w_err * 100:.1f}%）／表II 一致 {agree * 100:.0f}%")
    print("冒頭（〜T_MOVE）の着地 [枚数, バターが下]:", deco_down_share())
    run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 1.0, 2.5, 4.0, 8.6, 9.6, 10.6, 11.6, 12.4, 14.0, 16.0, 18.6, 20.0,
              22.0, 23.5, 25.0, 27.5, 29.0, 30.5, 32.0, 33.5, 35.0, 36.5]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
