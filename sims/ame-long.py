"""傘をさしたら、走ると濡れる？ 傘ありで100m、1万人が思い思いの速さで。（横型ロング）— 2026-10-11 作成（公開予定 10/24）

このファイルは公開日まで非公開（答えが書いてある）。上半分がモデル（数字の計算・照合・数字の書き出し）、後ろが場面（描画・音・書き出し）。
構成案: publish/ame-long/outline.md ／ 元のショート: sims/ame-hashiru.py（触らない）

モデル（雨・体・動きはショートと同じ。そこに傘の円板を足す）
  座標    : 体の中心の真下の地面が原点。x＝進む向き（前が +x）、y＝横、z＝上。体に乗った目で見る（体は止まり、雨が動いてくる）。
  雨      : 1時間に10mm、粒は直径2mmの球で落ちる速さ U=6.49 m/s（Gunn & Kinzer 1949）。数密度 n = 約102個/m³、空間にでたらめ（ポアソン）。
            風 w（進む向きを正）のとき、雨粒は水平に w で流れる。体から見た雨粒の速さ = (c, 0, −U)、c = w − v（v は進む速さ）。
            c < 0 なら雨は前から、c > 0 なら後ろから向かってくる。
  人      : 直方体。幅（y）0.45m × 奥行き（x）0.25m × 高さ（z）1.7m。体の中心は x=0（前の面は x=+0.125、後ろの面は x=−0.125）。
            雨粒には横向きの速さがないので、体の横の面には雨が当たらない（横の面 = 0粒）。当たるのは上の面と、前（c<0）か後ろ（c>0）の面だけ。
  傘      : 円板（直径 Du、中心は体の真上 (0, 0, Hu)）。前へ傾ける角度 φ（0＝水平、前の縁が下がる向きが +φ、後ろへ傾けるなら −φ）。
            円板の法線 n = (sin φ, 0, cos φ)。柄・持つ手は無視。本物の傘は椀形だが、円板に置き換える（縁の高さ付近を代表させる）。
            雨粒が体の箱に入る前に円板を通る（雨粒の直線が円板と交わる）と、その粒は傘に当たって体には来ない。
            傘は歩き出す前からさしている（定常状態）。傘の影にあった雨粒は、最初から無かったことにする（歩き出した瞬間の「傘の下の雨粒」は数えない）。
  動き    : 100m を一定の速さ v で進む（時間 T = 100/v）。
  数え方  : (a) 期待値（解析）… 体の表面を細かい格子（4mm）に切り、各点から雨の来る向きにさかのぼった直線が円板と交わるかを調べ、
                 交わらない（傘の影でない）面積に、雨の流れ込む量（上: n×U、前/後ろ: n×|c|）を掛けて、T 秒ぶんを足す。
            (b) モンテカルロ … 雨粒を空間にでたらめ（ポアソン）にまき、1粒ずつ動く箱に入る時刻・面を調べ、
                 入る前に円板と交わる粒を除いて数える（ショートの _drops / _test と同じ数え方に、円板との交わりと奥行き方向 y を足した）。
            1万人の分布は (b)（雨粒を実際にまく）で出す。速さごとの平均・最適な傾きなどの表の数字は (a)（速さをぴったり指定できるので、乱数のばらつきが載らない）。
            (b) は 1万人×8条件（傘なし/傘水平/傘最適傾き ×無風、傘なし・傘水平・傘最適傾き ×追い風、傘水平・傘最適傾き ×向かい風）と、別の乱数の1万人×3条件。
            各条件を数百人で (a) と照合し、1万人は『人ごとの期待値＋ポアソンのばらつき』にも照合。
  答えの照合に使う式（傘なしのとき）:
            当たる粒の期待値 = n × 幅 × T × ( 奥行き×落ちる速さ + 高さ×|w − v| )   （ショートと同じ。Du=0 で (a) がこれに一致）

台本の章と、ここで作るもの（概要は out/ame-long/numbers.md）
  1章: 傘あり・無風・水平。歩き/走りの粒数、傘なしとの比、1万人の速さごとの平均、どの速さが一番濡れないか
  2章: どこに当たるか（上・前・後ろ・横、高さ別、前面の濡れる高さ）
  3章: 前に傾ける。速さごとの最適な傾き φ* と粒数。雨の見かけの角度との比較
  4章: 傘の大きさ（長傘 1.0m／折りたたみ 0.9m／ゴルフ傘 1.2m）、持つ高さの感度
  5章: 風（追い風3m/s・向かい風3m/s）
  6章: まとめ用の数字

使い方
  python -X utf8 sims/ame-long.py --check      照合だけ（キャッシュを使う）
  python -X utf8 sims/ame-long.py --numbers    数字の書き出し（out/ame-long/numbers.md）
  python -X utf8 sims/ame-long.py --recompute  キャッシュを捨てて全部やり直す
  python -X utf8 sims/ame-long.py --check --numbers  照合 → numbers.md
  場面（描画）の使い方はファイルの最後（--readings / --stills / --preview / 引数なしで本番）
乱数の種は、画面の見本（1人ぶん）を「ふつうの結果」にするために選んでよい（描画担当が後で）。画面の統計は全員から正直に出している。
"""
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers

SLUG = "ame-long"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ============================================================
# モデルの値（雨・体・動きはショート sims/ame-hashiru.py と同じ）
# ============================================================
D = 100.0                                         # 道のり（m）
U = 6.49                                          # 雨粒の落ちる速さ（m/s）Gunn & Kinzer 1949: 直径2mm
DIA = 2.0e-3
RAIN_MMH = 10.0
DROP_VOL = math.pi / 6 * DIA ** 3
NDENS = (RAIN_MMH / 1000 / 3600) / (U * DROP_VOL)  # 約102個/m³
BW, BL, BH = 0.45, 0.25, 1.70                     # 人: 幅・奥行き・高さ（m）
A_TOP, A_FRONT = BW * BL, BW * BH
WIND = 3.0                                        # 風の速さ（m/s）。追い風 = +3、向かい風 = −3
V_WALK, V_RUN = 1.4, 5.0
V_LO, V_HI = 1.0, 7.0
N_PEOPLE = 10000
V_LIST = (1.0, 1.4, 2.0, 3.0, 4.0, 5.0, 7.0)      # 表に出す速さ
V_LIST_BIN = (1.4, 2.0, 3.0, 4.0, 5.0, 7.0)       # 「1万人の平均を速さごとに」の速さ（指定どおり）

# ---- 傘の寸法（WebSearch、2026-10-11。出典は numbers.md に再掲）----
#   直径: 親骨60cm の長傘の開いた直径は 約100〜107cm（my-best.com/21654 の商品表: 101〜107cm）、親骨55cm の折りたたみは 約97cm（無印良品）、
#         親骨50cm で 約80〜90cm、親骨65cm のゴルフ傘で 約110〜115cm、70cm で 約120〜125cm。
#   持つ高さ（円板の高さ）: 検索では分からなかった（頭からの距離を載せた情報源なし）→ 仮。
#         長傘の全長（閉じたとき）約85〜87cm、手は柄の端近く → 手の高さ約1.2〜1.3m として、てっぺん 約1.95〜2.0m、縁（椀の下端）はそれより約0.1〜0.2m低い。
#         円板は縁と頂点の間を代表させて 1.9m（構成案の試算と同じ。身長1.7mの人の頭の上20cm）。
UMBRELLAS = {"長傘": (1.0, 1.9), "折りたたみ傘": (0.9, 1.9), "ゴルフ傘": (1.2, 1.9)}   # (直径 Du, 円板の高さ Hu)。折りたたみ・ゴルフの高さは長傘と同じ（直径だけを変えて比べる）
DU, HU = UMBRELLAS["長傘"]
HU_LIST = (1.8, 1.9, 2.0)                         # 持つ高さの感度
DU_SWEEP = (0.0, 0.6, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4)
PHI_MAX = 55.0                                    # 傾けられる範囲（度）。円板が体の頭（x=±0.125）の高さ1.7mより下がらない限界 atan((Hu−1.7)/0.125)≒58度の手前

CELL = 0.004                                      # 期待値（解析）の格子（m）
CELL_SEARCH = 0.008                               # 最適な傾き探索の粗い格子


# ============================================================
# 1. 傘の影の幾何と期待値 (a)
# ============================================================
def apparent_angle(v, w=0.0):
    """雨の見かけの角度（度）。鉛直から、体から見た雨の向きまで"""
    return math.degrees(math.atan(abs(w - v) / U))


def blocked_pts(px, py, pz, c, Du, Hu, phi_deg, cx=0.0):
    """点 (px,py,pz) から雨の来る向きにさかのぼった直線が、傘の円板と交わるか（＝その点は傘の影か）"""
    if Du <= 0:
        return np.zeros(np.broadcast(px, py, pz).shape, bool)
    ph = math.radians(phi_deg)
    sp, cp = math.sin(ph), math.cos(ph)
    den = U * cp - c * sp                         # n · (さかのぼる向き (−c,0,U))
    s = (sp * (cx - px) + cp * (Hu - pz)) / den
    qx = px - c * s - cx
    qz = pz + U * s - Hu
    return (s > 0) & (qx * qx + py * py + qz * qz <= (Du / 2) ** 2)


_GRID = {}


def grid(cell):
    """体の表面の格子（y は 0〜幅/2 の半分だけ。左右対称なので2倍する）"""
    if cell not in _GRID:
        nx = max(1, int(round(BL / cell)))
        ny = max(1, int(round((BW / 2) / cell)))
        nz = max(1, int(round(BH / cell)))
        xt = -BL / 2 + (np.arange(nx) + 0.5) * (BL / nx)
        yy = (np.arange(ny) + 0.5) * ((BW / 2) / ny)
        zz = (np.arange(nz) + 0.5) * (BH / nz)
        TX, TY = np.meshgrid(xt, yy, indexing="ij")
        FY, FZ = np.meshgrid(yy, zz, indexing="ij")
        _GRID[cell] = dict(TX=TX, TY=TY, FY=FY, FZ=FZ, dA_top=(BL / nx) * ((BW / 2) / ny) * 2,
                           dA_face=((BW / 2) / ny) * (BH / nz) * 2, dz=BH / nz, zz=zz, yy=yy, ny=ny)
    return _GRID[cell]


def expected(v, w=0.0, Du=0.0, Hu=HU, phi=0.0, cell=CELL, detail=False, d=None, cx=0.0):
    """当たる粒の期待値 (a)。v は速さ（スカラー）。detail=True なら内訳（上・前/後ろ・高さ別）も返す"""
    d = D if d is None else d
    c = w - v
    T = d / v
    g = grid(cell)
    nT = NDENS * T
    # 上の面
    bt = blocked_pts(g["TX"], g["TY"], BH, c, Du, Hu, phi, cx)
    top_wet_area = float((~bt).sum()) * g["dA_top"]
    top = nT * U * top_wet_area
    # 前（c<0）か後ろ（c>0）の面
    face = 0.0
    wet_z = None
    if abs(c) > 1e-12:
        px = BL / 2 if c < 0 else -BL / 2
        bf = blocked_pts(px, g["FY"], g["FZ"], c, Du, Hu, phi, cx)
        wet = ~bf
        face = nT * abs(c) * float(wet.sum()) * g["dA_face"]
        wet_z = wet.mean(axis=0)                  # 高さの行ごとに、横方向のうち濡れる割合
    total = top + face
    if not detail:
        return total
    out = dict(total=total, top=top, face=face, side=0.0, face_kind=("前" if c < 0 else ("後ろ" if c > 0 else "なし")),
               top_wet_frac=top_wet_area / A_TOP, face_wet_frac=(float(wet_z.mean()) if wet_z is not None else 0.0))
    if wet_z is not None:
        zz, dz = g["zz"], g["dz"]
        wet = ~bf
        # 中心線（y≈0）と端（y=幅/2）で、その高さより下が濡れる「境の高さ」（その高さの行より上は乾いている）
        out["z_dry_center"] = _dry_from(wet[0], zz, dz)
        out["z_dry_edge"] = _dry_from(wet[-1], zz, dz)
        out["bands"] = {f"{lo:.1f}-{hi:.1f}": nT * abs(c) * BW * float((wet_z * ((zz >= lo) & (zz < hi))).sum()) * dz
                        for lo, hi in ((0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, BH + 1e-9))}
        out["wet_z"] = wet_z
    else:
        out["z_dry_center"] = out["z_dry_edge"] = 0.0
        out["bands"] = {k: 0.0 for k in ("0.0-0.5", "0.5-1.0", "1.0-1.5", "1.5-1.7")}
    return out


def _dry_from(wet_col, zz, dz):
    """高さの列（下から上）で、「ここより上は全部乾いている」最も低い高さ。全部乾いていれば 0、いちばん上まで濡れるなら BH"""
    idx = np.flatnonzero(wet_col)
    if idx.size == 0:
        return 0.0
    return float(min(BH, zz[idx[-1]] + dz / 2))


def perp_angle(v, w=0.0):
    """雨に垂直に向ける傾き（度）。符号つき: 雨が前から来る（v > w）なら前へ傾ける（+）、後ろから来るなら後ろへ（−）"""
    return math.degrees(math.atan((v - w) / U))


def best_tilt(v, w=0.0, Du=DU, Hu=HU):
    """一番濡れない傾き φ*（度）と、そのときの粒数。
    傘の中心は体の真上に固定なので、雨の向きに沿って体へ落ちる傘の影は、どの傾きでも同じ中心の楕円（長さ方向 R·cos(雨と法線の角)、幅方向 R）。
    雨に垂直（法線 ∥ 雨）のとき円（半径 R）になり、ほかの傾きの楕円はすべてその円の内側 → 垂直のときが影の面積・範囲とも最大 → 濡れ方は最小。
    つまり φ* = 雨の見かけの角度（ぴったり）。傾けられる範囲は ±PHI_MAX まで（これ以上は傘が頭にぶつかる）。照合 best_tilt_numeric で格子探索とも一致を確かめる"""
    ph = max(-PHI_MAX, min(PHI_MAX, perp_angle(v, w)))
    return float(ph), expected(v, w, Du, Hu, ph)


def best_tilt_numeric(v, w=0.0, Du=DU, Hu=HU, step=1.0):
    """照合用: 傾きを格子で探して、いちばん粒数が少ない傾きと粒数（解析 best_tilt の独立な確かめ）"""
    phis = np.arange(-PHI_MAX, PHI_MAX + 1e-9, step)
    vals = np.array([expected(v, w, Du, Hu, p, cell=CELL_SEARCH) for p in phis])
    k = int(np.argmin(vals))
    return float(phis[k]), float(vals[k])


def floor_hits():
    return NDENS * A_FRONT * D


def expected_plain(v, w=0.0):
    """傘なしの式（ショートと同じ）"""
    v = np.asarray(v, dtype=float)
    return NDENS * BW * (D / v) * (BL * U + BH * np.abs(w - v))


# ============================================================
# 2. 雨粒を実際にまく (b)
# ============================================================
def _drops(c, T, rng, dx=0.2):
    """この人に当たりうる範囲に雨粒をまく（x 方向の列ごとに、当たりうる高さの範囲にだけまく。y は体の幅の中）"""
    if abs(c) < 1e-6:
        c = 1e-6 if c >= 0 else -1e-6
    h = BL / 2
    xa = -h - max(0.0, c * T)
    xb = h - min(0.0, c * T)
    nb = int(math.ceil((xb - xa) / dx))
    e0 = xa + dx * np.arange(nb)
    e1 = np.minimum(e0 + dx, xb)

    def tx(x):
        ta, tb = (-h - x) / c, (h - x) / c
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
    y0 = (rng.random(len(idx)) - 0.5) * BW
    return x0, y0, z0, c


def _test(x0, y0, z0, c, T, Du, Hu, phi_deg, cx=0.0):
    """1粒ずつ、動く箱に入るかを調べ、入る前に傘の円板を通る粒を除く。返り値: 当たったか, 入った時刻, 上から入ったか"""
    h = BL / 2
    ta, tb = (-h - x0) / c, (h - x0) / c
    txi, txo = np.minimum(ta, tb), np.maximum(ta, tb)
    tzi, tzo = (z0 - BH) / U, z0 / U
    ti, to = np.maximum(txi, tzi), np.minimum(txo, tzo)
    hit = (ti < to) & (ti > 0) & (ti <= T)
    if Du > 0 and hit.any():
        ph = math.radians(phi_deg)
        sp, cp = math.sin(ph), math.cos(ph)
        nu = c * sp - U * cp                      # n · u （u = (c,0,−U)。いつも負）
        tu = (sp * (cx - x0) + cp * (Hu - z0)) / nu
        qx = x0 + c * tu - cx
        qz = z0 - U * tu - Hu
        blk = (tu < ti) & (qx * qx + y0 * y0 + qz * qz <= (Du / 2) ** 2)
        hit = hit & ~blk
    return hit, ti, tzi > txi


def person_mc(v, w, seed, Du=0.0, Hu=HU, phi=0.0, record=False, cx=0.0):
    rng = np.random.default_rng(seed)
    T = D / v
    x0, y0, z0, c = _drops(w - v, T, rng)
    hit, ti, top = _test(x0, y0, z0, c, T, Du, Hu, phi, cx)
    if not record:
        return int(hit.sum())
    zi = z0[hit] - U * ti[hit]
    return dict(n=int(hit.sum()), top=int(top[hit].sum()), face=int((~top[hit]).sum()), z=zi[~top[hit]], c=c)


def _chunk(args):
    vs, w, seed, Du, Hu, phis = args
    out = np.empty(len(vs), np.int64)
    for k, v in enumerate(vs):
        out[k] = person_mc(float(v), w, seed * 100003 + k, Du, Hu, float(phis[k]))
    return out


def many_mc(vs, w, seed, Du=0.0, Hu=HU, phis=None, chunk=250):
    """vs の1人ずつを別々の乱数で。phis は人ごとの傾き（なければ全員 0）。別プロセスに分けて回す"""
    vs = np.asarray(vs, float)
    phis = np.zeros(len(vs)) if phis is None else np.asarray(phis, float)
    jobs = [(vs[i:i + chunk], w, seed * 1000 + i // chunk, Du, Hu, phis[i:i + chunk]) for i in range(0, len(vs), chunk)]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        return np.concatenate(list(ex.map(_chunk, jobs)))


def many_expected(vs, w, Du, Hu, phi_fn=None, cell=0.006, grid_v=None):
    """人ごとの期待値 (a)。速さ v の細かい格子で計算して補間する（1万人ぶんを直接計算しない）"""
    gv = np.arange(0.95, 7.06, 0.02) if grid_v is None else grid_v
    ge = np.array([expected(v, w, Du, Hu, (phi_fn(v) if phi_fn else 0.0), cell=cell) for v in gv])
    return np.interp(vs, gv, ge), gv, ge





# ============================================================
# 3. 章ごとの計算
# ============================================================
def _round_disp(x):
    """画面に出す丸め: 1000以上は100粒単位、未満は10粒単位"""
    x = float(x)
    return round(x / 100) * 100 if x >= 1000 else round(x / 10) * 10


def detail_row(v, w, Du, Hu, phi):
    d = expected(v, w, Du, Hu, phi, detail=True)
    d.pop("wet_z", None)
    return d


def tilt_table(w, Du, Hu, vs):
    """速さごとの最適な傾き"""
    rows = []
    for v in vs:
        ph, e = best_tilt(v, w, Du, Hu)
        rows.append(dict(v=float(v), phi=ph, e=e, e0=expected(v, w, Du, Hu, 0.0), plain=float(expected_plain(v, w))))
    return rows


def phi_interp(w, Du, Hu, step=0.1):
    """最適な傾き（雨に垂直）を、速さ 0.9〜7.1 の格子で。人ごとに傾きを変える計算用"""
    gv = np.arange(0.9, 7.1 + 1e-9, step)
    gp = np.array([best_tilt(float(v), w, Du, Hu)[0] for v in gv])
    return gv, gp


def zero_ranges(w, Du, Hu, phi=0.0, lo=0.2, hi=7.5, step=0.02):
    """期待値が 1粒未満になる速さの範囲（[下端, 上端] のリスト）。端は二分探索で詰める"""
    vs = np.arange(lo, hi + 1e-9, step)
    ok = np.array([expected(v, w, Du, Hu, phi) < 1.0 for v in vs])
    out, i = [], 0
    while i < len(vs):
        if ok[i]:
            j = i
            while j + 1 < len(vs) and ok[j + 1]:
                j += 1
            a0 = vs[i]
            if i > 0:
                x, y = vs[i - 1], vs[i]                  # x は 1粒以上、y は 1粒未満
                for _ in range(30):
                    m = (x + y) / 2
                    if expected(m, w, Du, Hu, phi) < 1.0:
                        y = m
                    else:
                        x = m
                a0 = y
            b0 = vs[j]
            if j + 1 < len(vs):
                x, y = vs[j], vs[j + 1]                  # x は 1粒未満、y は 1粒以上
                for _ in range(30):
                    m = (x + y) / 2
                    if expected(m, w, Du, Hu, phi) < 1.0:
                        x = m
                    else:
                        y = m
                b0 = x
            out.append([float(a0), float(b0)])
            i = j + 1
        else:
            i += 1
    return out


def bin_mask(vs, cen, half=0.1):
    return (vs >= cen - half) & ((vs < cen + half) if cen < V_HI - 1e-9 else (vs <= V_HI))


def bin_stats(vs, hs, cen, half=0.1):
    m = bin_mask(vs, cen, half)
    return float(hs[m].mean()), int(m.sum()), float(hs[m].std(ddof=1) / math.sqrt(m.sum()))


def compute_people(seed_v=1):
    """1万人 (b)。同じ速さの人たちで条件ごとに雨粒をまく。返り値: 速さの配列, 条件ごとの粒数, 条件ごとの人ごとの期待値"""
    rng = np.random.default_rng(seed_v)
    vs = V_LO + (V_HI - V_LO) * rng.random(N_PEOPLE)
    conds = [  # (名前, 風, Du, 傾き: None=水平 / "opt"=最適, 種)
        ("plain_calm", 0.0, 0.0, None, 11),
        ("plain_tail", WIND, 0.0, None, 12),
        ("flat_calm", 0.0, DU, None, 13),
        ("opt_calm", 0.0, DU, "opt", 14),
        ("flat_tail", WIND, DU, None, 15),
        ("flat_head", -WIND, DU, None, 16),
        ("opt_tail", WIND, DU, "opt", 17),
        ("opt_head", -WIND, DU, "opt", 18),
    ]
    hits, exps, phis_used = {}, {}, {}
    for name, w, du, tilt, sd in conds:
        t0 = time.time()
        if tilt == "opt":
            gv, gp = phi_interp(w, du, HU)
            phis = np.interp(vs, gv, gp)
            fn = lambda v, gv=gv, gp=gp: float(np.interp(v, gv, gp))
        else:
            phis, fn = None, None
        hits[name] = many_mc(vs, w, sd, du, HU, phis)
        exps[name] = many_expected(vs, w, du, HU, fn)[0]
        if phis is not None:
            phis_used[name] = phis
        print(f"  1万人 {name}: {time.time() - t0:.0f}秒", flush=True)
    return vs, hits, exps, phis_used, conds


def compute_again():
    """別の乱数で1万人をやり直す（画面の数字が同じ丸めか）。速さも別（種99）。傘なし・傘水平・傘最適傾き（無風）"""
    rng = np.random.default_rng(99)
    vs = V_LO + (V_HI - V_LO) * rng.random(N_PEOPLE)
    out = {}
    gv, gp = phi_interp(0.0, DU, HU)
    out["plain_calm"] = many_mc(vs, 0.0, 91, 0.0, HU)
    out["flat_calm"] = many_mc(vs, 0.0, 92, DU, HU)
    out["opt_calm"] = many_mc(vs, 0.0, 93, DU, HU, np.interp(vs, gv, gp))
    return vs, out


def compute():
    t_all = time.time()
    res = dict(params=dict(D=D, U=U, NDENS=NDENS, BW=BW, BL=BL, BH=BH, DU=DU, HU=HU, WIND=WIND, N_PEOPLE=N_PEOPLE, CELL=CELL))
    # ---------- 1章: 傘あり・無風・水平 ----------
    rows = []
    for v in V_LIST:
        pl, um = float(expected_plain(v)), expected(v, 0.0, DU, HU, 0.0)
        rows.append(dict(v=v, plain=pl, umb=um, ratio=(um / pl)))
    walk_pl, run_pl = float(expected_plain(V_WALK)), float(expected_plain(V_RUN))
    walk_um, run_um = expected(V_WALK, 0.0, DU, HU, 0.0), expected(V_RUN, 0.0, DU, HU, 0.0)
    fine_v = [round(x, 2) for x in np.arange(0.5, 7.51, 0.1)]
    curve = [dict(v=v, plain=float(expected_plain(v)), umb=expected(v, 0.0, DU, HU, 0.0)) for v in fine_v]
    vmin = min((c for c in curve if c["v"] >= V_LO - 1e-9), key=lambda c: c["umb"])
    ch1 = dict(rows=rows, walk_plain=walk_pl, run_plain=run_pl, walk_umb=walk_um, run_umb=run_um,
               cut_plain=1 - run_pl / walk_pl, run_over_walk_umb=run_um / walk_um, run_over_walk_plain=run_pl / walk_pl,
               zero=zero_ranges(0.0, DU, HU), vmin=vmin, curve=curve,
               umb_vs_plain_walk=walk_um / walk_pl, umb_vs_plain_run=run_um / run_pl,
               floor=floor_hits())
    res["ch1"] = ch1
    # ---------- 2章: どこに当たるか ----------
    ch2 = {}
    for v in (V_WALK, V_RUN):
        ch2[f"{v}"] = dict(plain=detail_row(v, 0.0, 0.0, HU, 0.0), umb=detail_row(v, 0.0, DU, HU, 0.0))
    res["ch2"] = ch2
    # ---------- 3章: 前に傾ける ----------
    vs3 = (1.0, 1.4, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)
    rows3 = []
    for r in tilt_table(0.0, DU, HU, vs3):
        v = r["v"]
        ap = apparent_angle(v)
        d = detail_row(v, 0.0, DU, HU, r["phi"])
        rows3.append(dict(**r, apparent=ap, e_perp=expected(v, 0.0, DU, HU, ap), top=d["top"], face=d["face"],
                          z_dry_center=d["z_dry_center"], z_dry_edge=d["z_dry_edge"], face_wet_frac=d["face_wet_frac"],
                          bands=d["bands"]))
    phi_curve = {}
    for v in (V_WALK, V_RUN):
        phi_curve[f"{v}"] = [dict(phi=float(p), e=expected(v, 0.0, DU, HU, float(p))) for p in np.arange(-10, 51, 1.0)]
    res["ch3"] = dict(rows=rows3, phi_curve=phi_curve)
    # ---------- 4章: 傘の大きさ ----------
    ch4 = dict(umbrellas={}, du_sweep=[], hu_sweep=[])
    for name, (du, hu) in UMBRELLAS.items():
        e = {}
        for tag, v in (("walk", V_WALK), ("run", V_RUN)):
            ph, es = best_tilt(v, 0.0, du, hu)
            dh = detail_row(v, 0.0, du, hu, 0.0)
            e[tag] = dict(v=v, flat=dh["total"], phi=ph, opt=es, z_dry_center=dh["z_dry_center"], z_dry_edge=dh["z_dry_edge"])
        e["Du"], e["Hu"] = du, hu
        e["zero"] = zero_ranges(0.0, du, hu)
        ch4["umbrellas"][name] = e
    for du in DU_SWEEP:
        row = dict(Du=du)
        for tag, v in (("walk", V_WALK), ("run", V_RUN)):
            ph, es = best_tilt(v, 0.0, du, HU) if du > 0 else (0.0, float(expected_plain(v)))
            row[tag] = dict(flat=expected(v, 0.0, du, HU, 0.0), phi=ph, opt=es)
        ch4["du_sweep"].append(row)
    for hu in HU_LIST:
        row = dict(Hu=hu)
        for tag, v in (("walk", V_WALK), ("run", V_RUN)):
            ph, es = best_tilt(v, 0.0, DU, hu)
            row[tag] = dict(flat=expected(v, 0.0, DU, hu, 0.0), phi=ph, opt=es)
        ch4["hu_sweep"].append(row)
    res["ch4"] = ch4
    # ---------- 5章: 風 ----------
    ch5 = {}
    for name, w in (("tail", WIND), ("head", -WIND)):
        rows = []
        for v in V_LIST:
            ph, es = best_tilt(v, w, DU, HU)
            rows.append(dict(v=v, plain=float(expected_plain(v, w)), flat=expected(v, w, DU, HU, 0.0), phi=ph, opt=es,
                             apparent=apparent_angle(v, w)))
        fine = [dict(v=v, plain=float(expected_plain(v, w)), flat=expected(v, w, DU, HU, 0.0)) for v in fine_v]
        ch5[name] = dict(w=w, rows=rows, fine=fine, zero_flat=zero_ranges(w, DU, HU))
    # 追い風で風と同じ速さ（3m/s）
    ch5["tail_match"] = dict(plain=float(expected_plain(WIND, WIND)), flat=expected(WIND, WIND, DU, HU, 0.0))
    # 追い風・傘なしの谷（細かい格子の最小）、傘ありの谷
    res["ch5"] = ch5
    # ---------- 1万人 (b) ----------
    print("1万人（雨粒をまく）…", flush=True)
    vs, hits, exps, phis_used, conds = compute_people()
    vs2, again = compute_again()
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / "data.npz", vs=vs, vs2=vs2, **{f"h_{k}": v for k, v in hits.items()}, **{f"e_{k}": v for k, v in exps.items()},
             **{f"phi_{k}": v for k, v in phis_used.items()}, **{f"again_{k}": v for k, v in again.items()})
    people = {}
    for name, w, du, tilt, sd in conds:
        h, e = hits[name], exps[name]
        z = (h - e) / np.sqrt(np.maximum(e, 1e-9))
        m = e > 5
        people[name] = dict(w=w, Du=du, tilt=tilt, mean=float(h.mean()), mean_exp=float(e.mean()), minimum=int(h.min()), maximum=int(h.max()),
                            z_mean=float(z[m].mean()), z_var=float(z[m].var()), n_z=int(m.sum()),
                            bins={f"{c}": dict(zip(("mean", "n", "se"), bin_stats(vs, h, c))) | dict(exp=float(e[bin_mask(vs, c)].mean()))
                                  for c in V_LIST_BIN},
                            dispersion=dict(sd=float(h.std(ddof=1))))
        if name in again or name == "plain_calm":
            pass
    for name, h in again.items():
        people[name]["again_bins"] = {f"{c}": dict(zip(("mean", "n", "se"), bin_stats(vs2, h, c))) for c in V_LIST_BIN}
    # 追い風の谷（傘なし・傘水平）: 0.2m/s 幅ごとの平均の最小
    cen = np.arange(V_LO, V_HI + 1e-9, 0.2)
    for name in ("plain_tail", "flat_tail"):
        means = np.array([hits[name][(vs >= c - 0.1) & (vs < c + 0.1)].mean() for c in cen])
        k = int(np.argmin(means))
        people[name]["valley"] = dict(v=float(cen[k]), n=float(means[k]))
    # 傘水平・無風: 速さごとの平均の最小
    means = np.array([hits["flat_calm"][(vs >= c - 0.1) & (vs < c + 0.1)].mean() for c in cen])
    people["flat_calm"]["curve_min"] = dict(v=float(cen[int(np.argmin(means))]), n=float(means.min()))
    # 粒数が0の人の割合（傘水平・無風）
    people["flat_calm"]["zero_frac"] = float((hits["flat_calm"] == 0).mean())
    people["flat_calm"]["zero_vmax"] = float(vs[hits["flat_calm"] == 0].max()) if (hits["flat_calm"] == 0).any() else 0.0
    res["people"] = people
    # ---------- (b) の内訳照合用: 上・前・高さ別（数百人）----------
    brk = {}
    for tag, v in (("walk", V_WALK), ("run", V_RUN)):
        recs = [person_mc(v, 0.0, 70000 + 31 * k + int(v * 10), DU, HU, 0.0, record=True) for k in range(400)]
        z = np.concatenate([r["z"] for r in recs])
        brk[tag] = dict(n=len(recs), top=float(np.mean([r["top"] for r in recs])), face=float(np.mean([r["face"] for r in recs])),
                        bands={f"{lo:.1f}-{hi:.1f}": float(((z >= lo) & (z < hi)).sum() / len(recs))
                               for lo, hi in ((0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, BH + 1e-9))})
    res["breakdown_mc"] = brk
    # ---------- 6章: まとめ ----------
    c3 = {f"{r['v']}": r for r in res["ch3"]["rows"]}
    res["ch6"] = dict(
        plain_cut=ch1["cut_plain"], plain_walk=walk_pl, plain_run=run_pl,
        umb_walk=walk_um, umb_run=run_um, umb_ratio=run_um / walk_um,
        umb_opt_walk=c3["1.4"]["e"], umb_opt_run=c3["5.0"]["e"], umb_opt_phi_walk=c3["1.4"]["phi"], umb_opt_phi_run=c3["5.0"]["phi"],
        opt_ratio=c3["5.0"]["e"] / c3["1.4"]["e"],
        walk_umb_vs_plain_run=walk_um / run_pl,                       # 傘ありで歩く ÷ 傘なしで走る
        walk_opt_vs_plain_run=c3["1.4"]["e"] / run_pl,
        run_umb_vs_plain_run=run_um / run_pl,
        run_opt_vs_plain_run=c3["5.0"]["e"] / run_pl,
        run_umb_vs_plain_walk=run_um / walk_pl)
    res["ch4b"] = compute_arm()
    res["elapsed"] = time.time() - t_all
    return res


# ============================================================
# 3b. 腕の届く範囲で傘を動かす (ii)（2026-10-11 追加。4章（改））
#   (i)  今のモデル : 傘の中心は体の真上（0, 1.9m）に固定で、傾けるだけ（柄の長さ・手の位置は考えない）
#   (ii) このモデル : 手を肩から腕の長さ以内の好きな所（体の前半分）に置き、傘の円板は柄に垂直。
#                    手 H、柄の傾き φ（前へ）、柄の長さ Ls から、円板の中心 C = H + Ls·(sin φ, cos φ)。
#                    手・φ を全部探して、一番濡れない置き方を見つける。傘（円板）が頭や体に近づきすぎる置き方は除く。
#   座標は体の真横から見た断面 (x, z)。手は体の中心の面（y=0）に置くと近似する（本物は肩の横に腕が出るので、実際の届く距離はこれよりやや短い）
# ============================================================
ARM = 0.60                 # 肩（握る手）までの腕の長さ（m）。上肢長（肩峰〜指先）の日本人成人 男性715mm・女性645mm（中央値）− 手の中心から指先まで約9cm
SHOULDER_Z = 1.45          # 肩の高さ（m）。依頼どおり。肩峰高は一般に身長の約8割（1.7mなら約1.36m）だが、数値の出典は見つからなかった
SHOULDER = (0.0, SHOULDER_Z)
LS = 0.65                  # 手から円板の中心までの柄の長さ（m）。仮。水平（柄が鉛直）で円板が 1.9m になる手の高さ 1.25m から逆算
CLEAR = 0.10               # 円板が頭・体に近づける限界（m）。本物の傘は椀形で縁が下がるので、体の箱を10cm太らせた外側に円板を置く
ARM_PHI_LO, ARM_PHI_HI = -40.0, 70.0


def center_from_hand(hx, hz, phi, ls=LS):
    ph = math.radians(phi)
    return hx + ls * math.sin(ph), hz + ls * math.cos(ph)


def hand_from_center(cx, cz, phi, ls=LS):
    ph = math.radians(phi)
    return cx - ls * math.sin(ph), cz - ls * math.cos(ph)


def in_reach(hx, hz, arm=ARM, sz=SHOULDER_Z, behind=False):
    """手が体の前半分（x ≥ 0。behind=True なら後ろ半分も可）で、肩から腕の長さ以内か"""
    return (hx >= -1e-9 or behind) and math.hypot(hx, hz - sz) <= arm + 1e-9


_DISC_PTS = {}


def disc_hits_body(cx, cz, phi, Du, clear=CLEAR):
    """円板が、体の箱（clear だけ太らせたもの）にめり込むか"""
    if Du <= 0:
        return False
    if Du not in _DISC_PTS:
        r = np.linspace(0.0, Du / 2, 13)
        a = np.linspace(0.0, 2 * math.pi, 36, endpoint=False)
        R, A = np.meshgrid(r, a, indexing="ij")
        _DISC_PTS[Du] = (R * np.cos(A), R * np.sin(A))
    u, yy = _DISC_PTS[Du]
    ph = math.radians(phi)
    x = cx + u * math.cos(ph)
    z = cz - u * math.sin(ph)
    inside = (np.abs(x) <= BL / 2 + clear) & (np.abs(yy) <= BW / 2 + clear) & (z <= BH + clear) & (z >= -clear)
    return bool(inside.any())


def arm_value(v, w, Du, hx, hz, phi, arm=ARM, clear=CLEAR, sz=SHOULDER_Z, ls=LS, cell=CELL, behind=False):
    """手 (hx,hz)・柄の傾き phi の置き方の粒数。届かない・体にめり込む置き方は inf"""
    if not in_reach(hx, hz, arm, sz, behind):
        return math.inf
    cx, cz = center_from_hand(hx, hz, phi, ls)
    if disc_hits_body(cx, cz, phi, Du, clear):
        return math.inf
    e = expected(v, w, Du, cz, phi, cell=cell, cx=cx)
    # 同じ粒数（0粒など）が並ぶときの決め手: 傘の高さが普段の 1.9m に近い置き方・雨に垂直に近い傾きを、ごくわずかに好む
    return e + 1e-3 * abs(cz - HU) + 1e-3 * abs(phi - perp_angle(v, w)) / 90.0


def arm_search(v, w, Du, arm=ARM, clear=CLEAR, sz=SHOULDER_Z, ls=LS, behind=False):
    """手の位置（肩から腕の長さ以内・体の前半分）と柄の傾き φ を全部探して、一番濡れない置き方を返す。
    粗い格子（手: 肩から極座標 5cm×15度、φ: 5度刻み＋雨に垂直な角度）→ 上位の候補から細かい探索（パターン探索）。"""
    th = perp_angle(v, w)
    hands = [(0.0, sz)]
    for rr in np.arange(0.05, arm + 1e-9, 0.05):
        for ang in (np.arange(-180.0, 180.0, 15.0) if behind else np.arange(-90.0, 90.1, 15.0)):
            hx, hz = rr * math.cos(math.radians(ang)), sz + rr * math.sin(math.radians(ang))
            if in_reach(hx, hz, arm, sz, behind):
                hands.append((hx, hz))
    phis = sorted(set(list(np.arange(ARM_PHI_LO, ARM_PHI_HI + 1e-9, 5.0)) + [round(th, 3)]))
    cand = []
    for ph in phis:
        for hx, hz in hands:
            val = arm_value(v, w, Du, hx, hz, ph, arm, clear, sz, ls, cell=0.012, behind=behind)
            if val < math.inf:
                cand.append((val, hx, hz, ph))
    cand.sort(key=lambda t: t[0])
    best = None
    seen = []
    for val, hx, hz, ph in cand:
        if len(seen) >= 4:
            break
        if any(abs(hx - a) < 0.1 and abs(hz - b) < 0.1 and abs(ph - c) < 10 for a, b, c in seen):
            continue
        seen.append((hx, hz, ph))
        x, y, p = hx, hz, ph
        for cell_, s0x, s0p in ((0.006, 0.04, 3.0), (0.003, 0.01, 1.0)):      # 粗い格子で探したあと、細かい格子で詰める（格子のでこぼこを拾わないため）
            cur = arm_value(v, w, Du, x, y, p, arm, clear, sz, ls, cell=cell_, behind=behind)
            sx_, sp_ = s0x, s0p
            while sx_ > s0x / 10:
                improved = False
                for dx, dz, dp in ((sx_, 0, 0), (-sx_, 0, 0), (0, sx_, 0), (0, -sx_, 0), (0, 0, sp_), (0, 0, -sp_),
                                   (sx_, sx_, 0), (-sx_, -sx_, 0), (sx_, -sx_, 0), (-sx_, sx_, 0)):
                    t = arm_value(v, w, Du, x + dx, y + dz, p + dp, arm, clear, sz, ls, cell=cell_, behind=behind)
                    if t < cur - 1e-9:
                        x, y, p, cur, improved = x + dx, y + dz, p + dp, t, True
                if not improved:
                    sx_, sp_ = sx_ / 2, sp_ / 2
        if best is None or cur < best[0]:
            best = (cur, x, y, p)
    _, hx, hz, ph = best
    cx, cz = center_from_hand(hx, hz, ph, ls)
    d = expected(v, w, Du, cz, ph, detail=True, cx=cx, cell=0.002)
    d.pop("wet_z", None)
    return dict(v=float(v), w=float(w), Du=float(Du), e=d["total"], hand=[float(hx), float(hz)], phi=float(ph), theta=float(th),
                center=[float(cx), float(cz)], top=d["top"], face=d["face"], face_kind=d["face_kind"], face_wet_frac=d["face_wet_frac"],
                z_dry_center=d["z_dry_center"], z_dry_edge=d["z_dry_edge"], bands=d["bands"],
                reach=float(math.hypot(hx, hz - sz)), arm=arm, clear=clear, behind=bool(behind))


def d_need(theta_deg):
    """体を雨の向きに投影した長方形（幅 BW × 長さ BH·sinθ+BL·cosθ）を覆える円板の最小の直径"""
    t = math.radians(abs(theta_deg))
    return math.sqrt(BW ** 2 + (BH * math.sin(t) + BL * math.cos(t)) ** 2)


def _arm_case(a):
    v, w, Du, arm, clear, sz, ls = a[:7]
    return arm_search(v, w, Du, arm, clear, sz, ls, behind=(len(a) > 7 and a[7]))


def compute_arm_behind():
    """風3m/s: 手を体の後ろ半分にも置いてよい版 (ii')。追い風で雨が後ろから来るときは傘を後ろへ出せる"""
    keys = [(k, v) for k in ("tail", "head") for v in V_LIST_BIN]
    jobs = [(v, WIND if k == "tail" else -WIND, DU, ARM, CLEAR, SHOULDER_Z, LS, True) for k, v in keys]
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        outs = list(ex.map(_arm_case, jobs))
    res = {"tail": [], "head": []}
    for (k, v), r in zip(keys, outs):
        w = WIND if k == "tail" else -WIND
        ip, ie = best_tilt(v, w, DU, HU)
        res[k].append(dict(v=v, i=dict(phi=ip, e=ie, plain=float(expected_plain(v, w))), iib=r))
    return res


def compute_arm():
    t0 = time.time()
    jobs = {}

    def add(key, v, w, Du, arm=ARM, clear=CLEAR, sz=SHOULDER_Z, ls=LS):
        jobs[key] = (v, w, Du, arm, clear, sz, ls)
    for v in V_LIST_BIN:
        add(("calm", "長傘", v), v, 0.0, DU)
        add(("tail", "長傘", v), v, WIND, DU)
        add(("head", "長傘", v), v, -WIND, DU)
    for name in ("折りたたみ傘", "ゴルフ傘"):
        for v in V_LIST_BIN:
            add(("calm", name, v), v, 0.0, UMBRELLAS[name][0])
    for v in (V_WALK, V_RUN):
        for arm in (0.0, 0.4, 0.5, 0.7):
            add(("arm", arm, v), v, 0.0, DU, arm=arm)
        for cl in (0.05, 0.20):
            add(("clear", cl, v), v, 0.0, DU, clear=cl)
        for sz in (1.35, 1.55):
            add(("sz", sz, v), v, 0.0, DU, sz=sz)
        for ls in (0.55, 0.75):
            add(("ls", ls, v), v, 0.0, DU, ls=ls)
        add(("calm", "大きい傘1.4m", v), v, 0.0, 1.4)
    keys = list(jobs)
    with ProcessPoolExecutor(max_workers=max(1, min(12, (os.cpu_count() or 4) - 2))) as ex:
        outs = list(ex.map(_arm_case, [jobs[k] for k in keys]))
    R = dict(zip(keys, outs))

    def pick(prefix):
        return {k[2] if len(k) == 3 else k[1]: r for k, r in R.items() if k[:len(prefix)] == prefix}
    out = dict(params=dict(ARM=ARM, SHOULDER_Z=SHOULDER_Z, LS=LS, CLEAR=CLEAR, PHI_RANGE=[ARM_PHI_LO, ARM_PHI_HI]))
    rows = []
    for v in V_LIST_BIN:
        i_phi, i_e = best_tilt(v, 0.0, DU, HU)
        rr = R[("calm", "長傘", v)]
        rows.append(dict(v=v, i=dict(phi=i_phi, e=i_e, flat=expected(v, 0.0, DU, HU, 0.0), plain=float(expected_plain(v))), ii=rr,
                         d_need=d_need(perp_angle(v))))
    out["calm"] = rows
    out["umbrellas"] = {}
    for name in ("長傘", "折りたたみ傘", "ゴルフ傘", "大きい傘1.4m"):
        du = UMBRELLAS[name][0] if name in UMBRELLAS else 1.4
        lst = []
        for v in (V_LIST_BIN if name != "大きい傘1.4m" else (V_WALK, V_RUN)):
            r = R[("calm", name, v)]
            ip, ie = best_tilt(v, 0.0, du, HU)
            lst.append(dict(v=v, i=dict(phi=ip, e=ie), ii=r))
        out["umbrellas"][name] = dict(Du=du, rows=lst)
    for key in ("tail", "head"):
        w = WIND if key == "tail" else -WIND
        lst = []
        for v in V_LIST_BIN:
            ip, ie = best_tilt(v, w, DU, HU)
            lst.append(dict(v=v, i=dict(phi=ip, e=ie, plain=float(expected_plain(v, w))), ii=R[(key, "長傘", v)]))
        out[key] = lst
    sens = []
    for tag, label, keyname, vals in (("arm", "腕の長さ", "arm", (0.0, 0.4, 0.5, 0.7)), ("clear", "頭との余裕", "clear", (0.05, 0.20)),
                                      ("sz", "肩の高さ", "sz", (1.35, 1.55)), ("ls", "柄の長さ", "ls", (0.55, 0.75))):
        for val in vals:
            sens.append(dict(tag=tag, label=label, value=val, walk=R[(tag, val, V_WALK)], run=R[(tag, val, V_RUN)]))
    base = dict(walk=R[("calm", "長傘", V_WALK)], run=R[("calm", "長傘", V_RUN)])
    out["sens"] = sens
    out["sens_base"] = base
    # 結論: 走ると何倍か
    w_, r_ = base["walk"]["e"], base["run"]["e"]
    out["ratio_ii"] = (r_ / w_) if w_ > 0.5 else None
    out["wind_behind"] = compute_arm_behind()
    out["elapsed"] = time.time() - t0
    return out


def _jsonable(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def load(recompute=False):
    f = OUT / "data.json"
    if f.exists() and not recompute and (OUT / "data.npz").exists():
        res = json.loads(f.read_text(encoding="utf-8"))
        pr = res.get("params", {})
        if pr.get("DU") == DU and pr.get("HU") == HU and pr.get("N_PEOPLE") == N_PEOPLE and pr.get("CELL") == CELL and pr.get("NDENS") == NDENS:
            if "ch4b" not in res and __name__ == "__main__":      # 腕を伸ばす版（4章改）だけ足す（子プロセスでは計算しない）
                print("腕を伸ばす版を計算します…", flush=True)
                res["ch4b"] = compute_arm()
                tmp = f.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=_jsonable), encoding="utf-8")
                os.replace(tmp, f)
            if "ch4b" in res and "wind_behind" not in res["ch4b"] and __name__ == "__main__":     # 手を後ろにも置ける版（風）だけ足す
                print("風・手を後ろにも置ける版を計算します…", flush=True)
                res["ch4b"]["wind_behind"] = compute_arm_behind()
                tmp = f.with_suffix(".json.tmp")
                tmp.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=_jsonable), encoding="utf-8")
                os.replace(tmp, f)
            return res
    print("計算します…", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    res = compute()
    f.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=_jsonable), encoding="utf-8")
    return res


# ============================================================
# 4. 照合（check_answers で全部通す。1つでも外れたら止まる）
# ============================================================
def mc_mean(v, w, Du, Hu, phi, n=400, seed=0):
    xs = np.array([person_mc(v, w, 880000 + 977 * k + seed, Du, Hu, phi) for k in range(n)], float)
    return float(xs.mean()), float(xs.std(ddof=1) / math.sqrt(n))


def _name(Du, w):
    return ("傘なし" if Du == 0 else f"傘{Du:g}m") + ("" if w == 0 else (" 追い風" if w > 0 else " 向かい風"))


def check(res):
    checks = []
    ch1, pe = res["ch1"], res["people"]
    # ---------- A. 傘なし（Du=0）で、ショートの式・数字と一致 ----------
    worst = 0.0
    for v in (1.0, 1.4, 2.0, 3.0, 5.0, 7.0):
        for w in (0.0, WIND, -WIND):
            a = expected(v, w, 0.0)
            b = float(expected_plain(v, w))
            worst = max(worst, abs(a - b))
    checks.append(("A1 傘なし: 格子の期待値 (a) とショートの式（6速さ×3風）の最大の差（粒）", worst, 0.0, 1e-6))
    checks += [
        ("A2 ショート: 歩き 1.4m/s の式の値 vs ショートの『約13,100粒』", float(expected_plain(V_WALK)), 13100.0, 60.0),
        ("A3 ショート: 走り 5m/s の式の値 vs ショートの『約9,300粒』", float(expected_plain(V_RUN)), 9300.0, 30.0),
        ("A4 ショート: 底（前から当たる分）vs ショートの『約7,800粒』", floor_hits(), 7800.0, 30.0),
        ("A5 ショート: 追い風 3m/s で 3m/s の谷の式の値 vs ショートの『式の最小 約2,500粒』", float(expected_plain(WIND, WIND)), 2500.0, 30.0),
        ("A6 ショート: 走ると歩きより『約3割減』（割合）", ch1["cut_plain"], 0.29, 0.015),
    ]
    pc = pe["plain_calm"]
    for c, ref in ((1.4, 13100.0), (3.0, 10300.0), (5.0, 9300.0), (7.0, 8900.0)):
        b = pc["bins"][f"{c}"]
        checks.append((f"A7 ショート: 傘なし1万人（雨粒をまく）の {c}m/s 付近の平均 vs ショートの数字", b["mean"], ref, max(4 * b["se"], 100.0)))
    pt = pe["plain_tail"]
    checks += [
        ("A8 ショート: 傘なし追い風の谷の速さ（m/s）", pt["valley"]["v"], WIND, 0.15),
        ("A9 ショート: 傘なし追い風の谷の高さ（粒）vs ショートの『約2,600粒』", pt["valley"]["n"], 2600.0, 120.0),
    ]
    # ---------- B. 傘の影の幾何（自明な場合・解析式） ----------
    checks += [
        ("B1 真上から降る（風3m/s・歩く速さ3m/s）・傘水平: 体は濡れない（期待値 (a)、粒）", expected(3.0, WIND, DU, HU, 0.0), 0.0, 1e-9),
        ("B1' 同じ条件を雨粒をまいて（100人）数える（粒）", float(sum(person_mc(3.0, WIND, 5000 + k, DU, HU, 0.0) for k in range(100))), 0.0, 0.0),
        ("B2 ほぼ止まっている（0.01m/s）・傘水平: 濡れない（粒）", expected(0.01, 0.0, DU, HU, 0.0), 0.0, 1e-9),
        ("B3 真上から降る・傘なし: 上だけ（n×幅×奥行き×U×T）に一致（粒）", expected(3.0, WIND, 0.0), NDENS * BW * BL * U * D / 3.0, 1e-6),
    ]
    for v in (1.4, 2.0, 3.0, 5.0, 7.0):
        c = abs(v)
        R = DU / 2
        z_c = HU - (R - BL / 2) * U / c
        z_e = HU - (math.sqrt(R * R - (BW / 2) ** 2) - BL / 2) * U / c
        d = expected(v, 0.0, DU, HU, 0.0, detail=True)
        checks.append((f"B4 傘水平・{v}m/s: 体の中心線で『これより上は乾く』高さ（m）が解析式 Hu−(R−奥行き/2)·U/|c| に一致（格子4mm）",
                       d["z_dry_center"], max(0.0, min(BH, z_c)), 0.006))
        checks.append((f"B5 傘水平・{v}m/s: 体の左右の端で『これより上は乾く』高さ（m）が解析式に一致",
                       d["z_dry_edge"], max(0.0, min(BH, z_e)), 0.012))
    e1 = expected(2.0, 0.0, DU, HU, 20.0)          # 前から（c=−2）・前へ20度
    e2 = expected(2.0, 4.0, DU, HU, -20.0)         # 後ろから（c=+2）・後ろへ20度（鏡に映した条件）
    checks.append(("B6 左右（前後）を鏡に映した条件は同じ粒数（c=−2・前へ20度 と c=+2・後ろへ20度、粒）", e1, e2, 1e-6))
    checks.append(("B7 とても大きな傘（直径5m）を雨に垂直に向ければ濡れない（走り、粒）", expected(5.0, 0.0, 5.0, HU, perp_angle(5.0)), 0.0, 1e-9))
    viol = 0
    for key in ("walk", "run"):
        for opt in ("flat", "opt"):
            vals = [r[key][opt] for r in res["ch4"]["du_sweep"]]
            viol += sum(1 for a, b in zip(vals, vals[1:]) if b > a + 1e-6)
    checks.append(("B8 傘が大きいほど粒数は減る（直径 0〜1.4m の掃引、増えた箇所の数）", float(viol), 0.0, 0.0))
    worst = 0.0
    for v, w in ((V_WALK, 0.0), (V_RUN, 0.0)):
        a, b = expected(v, w, DU, HU, 0.0, cell=0.004), expected(v, w, DU, HU, 0.0, cell=0.002)
        worst = max(worst, abs(a - b) / b)
    checks.append(("B9 格子の細かさ（4mm と 2mm）で粒数が変わらない（歩き・走りの相対差）", worst, 0.0, 0.003))
    # 最適な傾き = 雨に垂直、を格子の探索と照合
    for v, w in ((1.4, 0.0), (2.0, 0.0), (3.0, 0.0), (5.0, 0.0), (7.0, 0.0), (1.4, WIND), (5.0, WIND), (2.0, -WIND), (5.0, -WIND)):
        ph, e = best_tilt(v, w, DU, HU)
        phn = np.arange(-PHI_MAX, PHI_MAX + 1e-9, 1.0)
        vals = np.array([expected(v, w, DU, HU, float(p)) for p in phn])
        checks.append((f"B10 最適な傾き（雨に垂直）の粒数 ≦ 1度刻みの探索で最小のもの＋1粒（v={v}, 風{w:g}）", float(e <= vals.min() + 1.0), 1.0, 0.0))
        if e > 200 and abs(ph) < PHI_MAX - 0.5:
            checks.append((f"B11 最適な傾き（度）が1度刻みの探索と2度以内で一致（v={v}, 風{w:g}）", ph, float(phn[int(np.argmin(vals))]), 2.0))
    # ---------- C. 期待値 (a) と、雨粒をまく数え方 (b) の一致 ----------
    cases = [
        (V_WALK, 0.0, DU, HU, 0.0), (V_RUN, 0.0, DU, HU, 0.0),
        (V_WALK, 0.0, DU, HU, best_tilt(V_WALK, 0.0)[0]), (V_RUN, 0.0, DU, HU, best_tilt(V_RUN, 0.0)[0]),
        (3.0, 0.0, DU, HU, 0.0), (2.0, 0.0, DU, HU, 20.0),
        (V_WALK, 0.0, 0.9, HU, 0.0), (V_RUN, 0.0, 1.2, HU, 0.0), (V_WALK, 0.0, DU, 1.8, 0.0),
        (V_WALK, WIND, DU, HU, 0.0), (V_RUN, WIND, DU, HU, best_tilt(V_RUN, WIND)[0]), (V_WALK, WIND, DU, HU, best_tilt(V_WALK, WIND)[0]),
        (3.0, WIND, DU, HU, 0.0), (2.0, -WIND, DU, HU, 0.0), (V_RUN, -WIND, DU, HU, best_tilt(V_RUN, -WIND)[0]),
        (V_WALK, 0.0, 0.0, HU, 0.0), (V_RUN, 0.0, 0.0, HU, 0.0), (3.0, WIND, 0.0, HU, 0.0),
    ]
    for i, (v, w, du, hu, ph) in enumerate(cases):
        m, se = mc_mean(v, w, du, hu, ph, 400, seed=i)
        e = expected(v, w, du, hu, ph)
        checks.append((f"C1 雨粒をまいた平均（400人）vs 期待値: v={v:g}m/s {_name(du, w)} Hu={hu:g} 傾き{ph:.1f}度（粒）", m, e, max(4 * se, 0.003 * e, 0.5)))
    brk = res["breakdown_mc"]
    for tag, v in (("walk", V_WALK), ("run", V_RUN)):
        d = res["ch2"][f"{v}"]["umb"]
        b = brk[tag]
        checks.append((f"C2 {tag}: 前の面に当たる粒（400人の平均）vs 期待値", b["face"], d["face"], 4 * math.sqrt(d["face"] / 400) + 0.003 * d["face"]))
        checks.append((f"C2 {tag}: 上の面に当たる粒（400人の平均）vs 期待値（傘が覆う → 0）", b["top"], d["top"], 0.5))
        for k, ev in d["bands"].items():
            checks.append((f"C3 {tag}: 高さ {k}m に当たる粒（400人の平均）vs 期待値", b["bands"][k], ev, 4 * math.sqrt(max(ev, 1.0) / 400) + 0.003 * ev + 0.5))
    # ---------- D. 1万人（雨粒をまく）が、人ごとの期待値＋ポアソンのばらつきに一致 ----------
    for name, p in pe.items():
        checks.append((f"D1 1万人 {name}: （粒数−人ごとの期待値）÷√期待値 の平均（0なら偏りなし）", p["z_mean"], 0.0, 0.05))
        checks.append((f"D2 1万人 {name}: 同じものの分散（ポアソンなら1）", p["z_var"], 1.0, 0.06))
        for c, b in p["bins"].items():
            checks.append((f"D3 1万人 {name}: {c}m/s 付近（±0.1）の平均 vs 同じ人たちの期待値の平均（粒）", b["mean"], b["exp"], max(4 * b["se"], 0.003 * b["exp"], 0.5)))
    fm = pe["flat_calm"]
    checks += [
        ("D4 傘水平・無風: 粒数が0の人はみな v0（=1.11m/s）以下", float(fm["zero_vmax"] <= ch1["zero"][0][1] + 0.01), 1.0, 0.0),
        ("D5 傘水平・無風: 粒数が0の人の割合 ≒ (v0−1)/6", fm["zero_frac"], (ch1["zero"][0][1] - V_LO) / (V_HI - V_LO), 0.006),
        ("D6 傘水平・追い風: 風と同じ 3m/s 付近の1万人の平均が0", pe["flat_tail"]["bins"]["3.0"]["mean"], 0.0, 0.5),
        ("D7 傘なし・無風の1万人は全員が『底』（前から当たる分）より上", 1.0, 1.0, 0.0),
    ]
    # D7 は実データで判定
    d = np.load(OUT / "data.npz")
    checks[-1] = ("D7 傘なし・無風の1万人は全員が『底』より上（約7,800粒）", float((d["h_plain_calm"] >= floor_hits() - 3 * math.sqrt(floor_hits())).all()), 1.0, 0.0)
    # ---------- E. 画面に出す数字の丸めが、別の乱数でも同じ ----------
    fences = []
    for name in ("plain_calm", "flat_calm", "opt_calm"):
        p = pe[name]
        for c in V_LIST_BIN:
            k = f"{c}"
            ex = {"plain_calm": float(expected_plain(c)), "flat_calm": expected(c, 0.0, DU, HU, 0.0), "opt_calm": best_tilt(c, 0.0)[1]}[name]
            r_ex = round(ex / 100) * 100.0
            for tag, bb in (("1万人", p["bins"][k]), ("別の乱数の1万人", p["again_bins"][k])):
                m, se = bb["mean"], bb.get("se", 0.0)
                checks.append((f"E1 100粒単位の丸め『約{r_ex:,.0f}』（ぴったりの速さの期待値 {ex:,.0f}）が {name} {c}m/s の{tag}（平均 {m:,.0f}）と矛盾しない（丸めの幅±50＋標準誤差の3倍）",
                               m, r_ex, 50.0 + 3 * se + abs(p["bins"][k]["mean"] - p["bins"][k]["exp"]) * (tag == "1万人")))
            if min(abs(ex - (r_ex - 50)), abs(ex - (r_ex + 50))) < 3 * p["bins"][k]["se"]:
                fences.append((name, c, ex, r_ex))
    res["fences"] = fences
    for name in ("plain_calm", "flat_calm", "opt_calm"):
        p = pe[name]
        r1_ = p["bins"]["5.0"]["mean"] / p["bins"]["1.4"]["mean"]
        r2_ = p["again_bins"]["5.0"]["mean"] / p["again_bins"]["1.4"]["mean"]
        re = {"plain_calm": ch1["run_plain"] / ch1["walk_plain"], "flat_calm": ch1["run_umb"] / ch1["walk_umb"],
              "opt_calm": res["ch6"]["umb_opt_run"] / res["ch6"]["umb_opt_walk"]}[name]
        if name == "plain_calm":
            checks.append(("E2 『走ると○割減』の○（整数に丸め）: 1万人の曲線 vs 別乱数 vs 式", float(round((1 - r1_) * 10)), float(round((1 - r2_) * 10)), 0.0))
            checks.append(("E2' 同じ ○ が式から出した値とも同じ", float(round((1 - r1_) * 10)), float(round((1 - re) * 10)), 0.0))
        else:
            checks.append((f"E3 『走ると歩きの○倍』の○（整数に丸め）: {name} 1万人の曲線 vs 別乱数", float(round(r1_)), float(round(r2_)), 0.0))
            checks.append((f"E3' 同じ ○ が式から出した値とも同じ: {name}", float(round(r1_)), float(round(re)), 0.0))
    # ---------- F. 答えの形 ----------
    checks += [
        ("F1 傘なしでは走るほうが少ない（歩き−走り > 0）", float(ch1["walk_plain"] > ch1["run_plain"]), 1.0, 0.0),
        ("F2 傘ありでは歩くほうが少ない（走り−歩き > 0）", float(ch1["run_umb"] > ch1["walk_umb"]), 1.0, 0.0),
        ("F3 傘ありで歩く < 傘なしで走る（傘は歩きなら効く）", float(ch1["walk_umb"] < ch1["run_plain"]), 1.0, 0.0),
        ("F4 傘ありで走っても傘なしで走るよりは少ない", float(ch1["run_umb"] < ch1["run_plain"]), 1.0, 0.0),
    ]
    if "ch4b" in res:
        checks += arm_checks(res)
    check_answers(checks)
    print(f"  照合 {len(checks)} 件 すべて OK")
    return len(checks)


# ============================================================
# 4b. 腕を伸ばす版 (ii) の照合と数字の書き出し
# ============================================================
def arm_checks(res):
    ab = res["ch4b"]
    checks = []
    # (1) (ii) の式で、手を『円板の中心が体の真上 (0, 1.9m)・最適な傾き』になる所に置くと (i) に一致する
    for v, w in ((V_WALK, 0.0), (V_RUN, 0.0), (3.0, 0.0), (V_RUN, WIND), (V_WALK, WIND), (V_RUN, -WIND)):
        ph, e_i = best_tilt(v, w, DU, HU)
        hx, hz = hand_from_center(0.0, HU, ph)
        cx, cz = center_from_hand(hx, hz, ph)
        e_ii = expected(v, w, DU, cz, ph, cx=cx)
        checks.append((f"G1 (ii) の式で手を {hx * 100:.0f}cm・{hz:.2f}m（中心が体の真上 1.9m）に置いた粒数 = (i)（v={v:g}, 風{w:g}、粒）", e_ii, e_i, 1e-6))
    # (2) 届く範囲の外・体の後ろ・めり込む置き方は選ばれない（inf）
    checks += [
        ("G2 肩から腕の長さを超える手の位置は選べない（inf なら 1）", float(arm_value(V_RUN, 0.0, DU, 0.5, 2.0, 30.0) == math.inf), 1.0, 0.0),
        ("G2' 体の後ろ（x<0）に手を置く置き方は選べない（inf なら 1）", float(arm_value(V_RUN, 0.0, DU, -0.1, 1.45, 30.0) == math.inf), 1.0, 0.0),
        ("G2'' 円板が頭にめり込む置き方（中心 1.75m・水平）は選べない（inf なら 1）", float(arm_value(V_WALK, 0.0, DU, 0.0, 1.75 - LS, 0.0) == math.inf), 1.0, 0.0),
        ("G2''' 届く範囲の中で、頭の上 2.0m に置いた置き方は選べる（有限なら 1）", float(arm_value(V_WALK, 0.0, DU, 0.2, 1.35, 0.0) < math.inf), 1.0, 0.0),
    ]
    allr = []
    for r in ab["calm"]:
        allr.append(r["ii"])
    for nm, u in ab["umbrellas"].items():
        allr += [x["ii"] for x in u["rows"]]
    for k in ("tail", "head"):
        allr += [x["ii"] for x in ab[k]]
    for s_ in ab["sens"]:
        allr += [s_["walk"], s_["run"]]
    wb = ab.get("wind_behind")
    if wb:
        for k in ("tail", "head"):
            allr += [x["iib"] for x in wb[k]]
    bad_reach = sum(1 for r in allr if r["reach"] > r["arm"] + 1e-6 or (r["hand"][0] < -1e-6 and not r.get("behind")))
    bad_body = 0
    for r in allr:
        if disc_hits_body(r["center"][0], r["center"][1], r["phi"], r["Du"], r["clear"]):
            bad_body += 1
    checks.append((f"G3 探索で選ばれた置き方 {len(allr)} 件のうち、腕の届かない・体の後ろのもの（件）", float(bad_reach), 0.0, 0.0))
    checks.append((f"G4 探索で選ばれた置き方 {len(allr)} 件のうち、傘が体にめり込むもの（件）", float(bad_body), 0.0, 0.0))
    # (3) 期待値 (a) と雨粒をまく (b) の一致（最適配置で）
    mc_cases = []
    for r in ab["calm"]:
        if r["v"] in (V_WALK, V_RUN, 3.0):
            mc_cases.append((r["ii"], DU))
    for nm in ("折りたたみ傘", "ゴルフ傘"):
        for x in ab["umbrellas"][nm]["rows"]:
            if x["v"] in (V_WALK, V_RUN):
                mc_cases.append((x["ii"], ab["umbrellas"][nm]["Du"]))
    for k in ("tail", "head"):
        for x in ab[k]:
            if x["v"] == V_RUN:
                mc_cases.append((x["ii"], DU))
    for i, (r, du) in enumerate(mc_cases):
        n = 400
        xs = np.array([person_mc(r["v"], r["w"], 990000 + 977 * k + i, du, r["center"][1], r["phi"], cx=r["center"][0]) for k in range(n)], float)
        m_, se = float(xs.mean()), float(xs.std(ddof=1) / math.sqrt(n))
        checks.append((f"G5 (ii) 最適配置を雨粒をまいて数えた平均（400人）vs 期待値: v={r['v']:g} 風{r['w']:g} 傘{du:g}m 手({r['hand'][0] * 100:.0f}cm, {r['hand'][1]:.2f}m) φ={r['phi']:.1f}°（粒）",
                       m_, expected(r["v"], r["w"], du, r["center"][1], r["phi"], cx=r["center"][0]), max(4 * se, 0.003 * r["e"], 0.5)))
    if wb:
        for k in ("tail", "head"):
            for x in wb[k]:
                r, r0 = x["iib"], next(y for y in ab[k] if y["v"] == x["v"])["ii"]
                checks.append((f"G11 手を後ろにも置ける版 ≦ 前だけの版（{k} {x['v']:g}m/s、探索の取りこぼし分 1%＋10粒を許す。超えた量）",
                               max(0.0, r["e"] - (r0["e"] + 0.01 * r0["e"] + 10)), 0.0, 0.0))
        for x in wb["tail"]:
            if x["v"] in (V_WALK, V_RUN, 7.0):
                r = x["iib"]
                xs = np.array([person_mc(r["v"], r["w"], 995000 + 977 * k, DU, r["center"][1], r["phi"], cx=r["center"][0]) for k in range(400)], float)
                checks.append((f"G12 追い風 v={r['v']:g} 手を後ろにも置ける最適配置（手 {r['hand'][0] * 100:.0f}cm, {r['hand'][1]:.2f}m, φ={r['phi']:.1f}°）を雨粒をまいた平均 vs 期待値（粒）",
                               float(xs.mean()), expected(r["v"], r["w"], DU, r["center"][1], r["phi"], cx=r["center"][0]),
                               max(4 * float(xs.std(ddof=1) / math.sqrt(400)), 0.003 * r["e"], 0.5)))
    # (4) 格子の細かさ
    worst = 0.0
    for r in ab["calm"]:
        if r["ii"]["e"] > 50:
            e2 = expected(r["v"], 0.0, DU, r["ii"]["center"][1], r["ii"]["phi"], cell=0.001, cx=r["ii"]["center"][0])
            worst = max(worst, abs(r["ii"]["e"] - e2) / e2)
    checks.append(("G6 格子2mm（報告値）と1mm（基準）で (ii) の粒数が変わらない（相対差の最大）", worst, 0.0, 0.006))
    # (5) 単調性: 腕が長いほど・傘が大きいほど減る（探索の取りこぼし分の許容 1%＋10粒）
    for tag, v in (("walk", V_WALK), ("run", V_RUN)):
        seq = [(0.0, [s_ for s_ in ab["sens"] if s_["tag"] == "arm" and s_["value"] == 0.0][0][tag]["e"])]
        for val in (0.4, 0.5):
            seq.append((val, [s_ for s_ in ab["sens"] if s_["tag"] == "arm" and s_["value"] == val][0][tag]["e"]))
        seq.append((ARM, ab["sens_base"][tag]["e"]))
        seq.append((0.7, [s_ for s_ in ab["sens"] if s_["tag"] == "arm" and s_["value"] == 0.7][0][tag]["e"]))
        viol = sum(1 for (a1, e1), (a2, e2) in zip(seq, seq[1:]) if e2 > e1 + 0.01 * e1 + 10)
        checks.append((f"G7 腕が長いほど粒数は減る（腕 0/0.4/0.5/0.6/0.7m、{tag}、増えた箇所）", float(viol), 0.0, 0.0))
    for v in (V_WALK, V_RUN):
        seq = [ab["umbrellas"][nm]["rows"][[x["v"] for x in ab["umbrellas"][nm]["rows"]].index(v)]["ii"]["e"] for nm in ("折りたたみ傘", "長傘", "ゴルフ傘")]
        seq.append(ab["umbrellas"]["大きい傘1.4m"]["rows"][[x["v"] for x in ab["umbrellas"]["大きい傘1.4m"]["rows"]].index(v)]["ii"]["e"])
        viol = sum(1 for e1, e2 in zip(seq, seq[1:]) if e2 > e1 + 0.01 * e1 + 10)
        checks.append((f"G8 傘が大きいほど (ii) の粒数は減る（0.9/1.0/1.2/1.4m、v={v:g}、増えた箇所）", float(viol), 0.0, 0.0))
    # (6) 0粒になれるのは、傘の直径が体の影を覆える大きさ以上のときだけ
    bad = 0
    for r in allr:
        if r["e"] < 0.5 and r["Du"] < d_need(r["theta"]) - 0.01:
            bad += 1
    checks.append(("G9 (ii) で0粒になった置き方のうち、傘の直径が体の影の最小の直径 √(幅²+(1.7·sinθ+0.25·cosθ)²) に足りないもの（件）", float(bad), 0.0, 0.0))
    # (7) 傘なしと (i) より悪くならない
    worse = 0
    for r in ab["calm"]:
        if r["ii"]["e"] > r["i"]["e"] + 0.01 * r["i"]["e"] + 10:
            worse += 1
    checks.append(("G10 (ii) が (i)（中心固定で傾ける）より多くなった速さの数（無風・長傘）", float(worse), 0.0, 0.0))
    return checks


SOURCES_ARM = [
    ("腕の長さ", "上肢長（肩峰〜指先、肘・手首を伸ばす）の日本人成人 中央値は男性715mm・女性645mm（5〜95%: 男665〜765、女605〜685）。"
     "傘の柄を握る手の中心は指先より約9cm手前（手長の約半分: 男性平均189.6mm）→ 肩から握りまで 男性約0.62m・女性約0.55m。**依頼どおり 0.60m を採用**（感度は表）",
     "https://personal.cityu.edu.hk/meachan/Online%20Anthropometry/Chapter2/Ch2-24.htm（香港城市大学の人体計測ページの日本人成人の表。元データの出典が明記されていない）／"
     "https://www.airc.aist.go.jp/dhrt/hand/data/all.pdf（産総研 日本人の手の寸法データ: 手長 男性189.6mm・女性175.4mm）。いずれも WebSearch の要約で確認（ページ本体は未取得）"),
    ("肩の高さ", "依頼どおり 1.45m。肩峰高の身長比の数値は検索で見つからなかった（一般に身長の約8割＝1.36m とされるが未確認）→ 感度 1.35／1.55m を表に", "（出典なし）"),
    ("手から円板の中心までの柄の長さ Ls", "**仮 0.65m**。水平（柄が鉛直）で円板が 1.9m になる手の高さ 1.25m（身長1.7mで肘を曲げて胸の前）から逆算。長傘は閉じて全長約85〜87cm → 開いて握りから縁まで約0.55m・てっぺんまで約0.75m の中間。感度 0.55／0.75m を表に", "（推定。出典なし）"),
    ("円板と体の余裕", "**仮 10cm**。本物の傘は椀形で縁が下がるので、円板を体の箱（幅0.45×奥行き0.25×高さ1.7m）より10cm外側に置く。感度 5cm／20cm を表に", "（推定。出典なし）"),
]


def write_arm_section(a, f0, res):
    ab = res["ch4b"]
    cm = lambda x: f"{x * 100:.0f}cm"
    a("## 4章（改）腕を伸ばして傾けたら")
    a("")
    a("依頼: 『傘を傾けるときは実際には傘を前に出す。人の手の届く範囲で伸ばすのを検証したい』。4章までの (i) は『傾けても傘の中心は体の真上に固定』なので、約1割しか減らず現実離れして見える。")
    a("")
    a("**(ii) 腕の届く範囲で動かすモデル**: 手を、肩（体の中心、高さ1.45m）から腕の長さ0.60m以内・体の前半分の好きな所に置く。傘の円板は柄に垂直で、"
      "柄の傾き φ（前へ）に対して円板の中心 C = 手 + 柄の長さ0.65m×(sin φ, cos φ)。手の位置と φ を全部探し（手: 肩から5cm×15度の格子→細かい探索、φ: −40〜70°）、"
      "一番濡れない置き方を選ぶ。円板が体の箱から10cm以内に近づく置き方は除く。座標は真横から見た断面で、手は体の中心の面に置くと近似（本物は肩の横に腕が出るので、実際の届く距離はこれよりやや短い）。")
    a("")
    a("### 値と出典")
    a("")
    for k, v, u in SOURCES_ARM:
        a(f"- **{k}**: {v}")
        a(f"  - 出典: {u}")
    a("")
    a("### 無風・長傘（直径1.0m）: (i) 中心固定で傾ける／(ii) 腕を伸ばして傾ける")
    a("")
    a("| 速さ | (i) φ* | (i) 粒 | (ii) 粒 | 手の位置（体の中心から前へ／高さ） | 柄の傾き φ（雨の角度 θ） | 傘の中心（前へ／高さ） | 前の面の濡れる面積 | 濡れる一番高い所（前の中心線〜端） | 体の影を覆える最小の直径 |\n|---|---|---|---|---|---|---|---|---|---|")
    for r in ab["calm"]:
        ii, i = r["ii"], r["i"]
        wet = "—（濡れない）" if ii["e"] < 0.5 else f"{cm(ii['z_dry_center'])}〜{cm(ii['z_dry_edge'])}"
        a(f"| {r['v']:g}m/s | {i['phi']:.1f}° | {f0(i['e'])} | **{f0(ii['e'])}** | {cm(ii['hand'][0])}／{ii['hand'][1]:.2f}m | {ii['phi']:.1f}°（{ii['theta']:.1f}°） | "
          f"{cm(ii['center'][0])}／{ii['center'][1]:.2f}m | {ii['face_wet_frac'] * 100:.0f}% | {wet} | {r['d_need']:.2f}m |")
    a("")
    wk = next(r for r in ab["calm"] if r["v"] == V_WALK)["ii"]
    rn = next(r for r in ab["calm"] if r["v"] == V_RUN)["ii"]
    wk_i = next(r for r in ab["calm"] if r["v"] == V_WALK)["i"]
    rn_i = next(r for r in ab["calm"] if r["v"] == V_RUN)["i"]
    a(f"- **歩き 1.4m/s**: (i) {f0(wk_i['e'])} → (ii) **{f0(wk['e'])} 粒**。傘の直径1.0mは体の影の最小 {next(r for r in ab['calm'] if r['v'] == V_WALK)['d_need']:.2f}m より大きいので、傘を雨に垂直に向けて体の真後ろの影に入れれば**0にできる**。"
      f"0になる置き方は幅広くある（表は『傘の高さが普段の1.9mに近く、雨に垂直に近い傾き』を選んだ一例: 手は前へ{cm(wk['hand'][0])}・高さ{wk['hand'][1]:.2f}m、傘の中心は前へ{cm(wk['center'][0])}・高さ{wk['center'][1]:.2f}m）。")
    a(f"- **走り 5m/s**: (i) {f0(rn_i['e'])} → (ii) **{f0(rn['e'])} 粒**（{(1 - rn['e'] / rn_i['e']) * 100:.0f}%減。傘なしの走り {f0(ch1_run(res))} の {rn['e'] / ch1_run(res) * 100:.0f}%）。"
      f"最適な置き方: 手は体の前へ{cm(rn['hand'][0])}・高さ{rn['hand'][1]:.2f}m（肩より{(res['ch4b']['params']['SHOULDER_Z'] - rn['hand'][1]) * 100:.0f}cm下）、柄を前へ{rn['phi']:.0f}°（雨の見かけの角度 {rn['theta']:.0f}°）、"
      f"傘の中心は体の前へ{cm(rn['center'][0])}・高さ{rn['center'][1]:.2f}m。")
    a(f"  - それでも**走ると足が濡れる**: 前は 足元〜{cm(rn['z_dry_center'])}（端は{cm(rn['z_dry_edge'])}）の高さが濡れる（前の面の{rn['face_wet_frac'] * 100:.0f}%）。"
      f"走り5m/sで雨は{rn['theta']:.0f}°から来て、体の影の長さは 1.7·sinθ＋0.25·cosθ ＝ {BH * math.sin(math.radians(rn['theta'])) + BL * math.cos(math.radians(rn['theta'])):.2f}m。"
      f"幅0.45mと合わせて覆うには直径 **{next(r for r in ab['calm'] if r['v'] == V_RUN)['d_need']:.2f}m 以上**が必要で、長傘1.0mでは足りない。")
    a("")
    a("### 結論は変わるか")
    a("")
    ratio = ab.get("ratio_ii")
    base = res["ch1"]
    if ratio is None:
        a(f"- **傘ありで『走ると何倍』**: (i) は {base['run_over_walk_umb']:.1f}倍（水平）／{rn_i['e'] / wk_i['e']:.1f}倍（傾ける）。(ii) は歩きが0粒になるので**倍率は定義できない（歩き0粒 → 走り{f0(rn['e'])}粒）**。")
    else:
        a(f"- **傘ありで『走ると何倍』**: (i) は {base['run_over_walk_umb']:.1f}倍（水平）／{rn_i['e'] / wk_i['e']:.1f}倍（傾ける）。(ii) は {ratio:.1f}倍。")
    a(f"- **向きは変わらない**: (ii) でも傘ありは歩くほうが少ない（歩き{f0(wk['e'])} < 走り{f0(rn['e'])}）。傘を前に出して傾けると、走りは約{(1 - rn['e'] / rn_i['e']) * 100:.0f}%減り、"
      f"傘なしで走る {f0(ch1_run(res))} の約{rn['e'] / ch1_run(res) * 100:.0f}%になるが、歩きはさらに0へ近づくので、差はむしろ開く。")
    big = next(x for x in ab["umbrellas"]["大きい傘1.4m"]["rows"] if x["v"] == V_RUN)["ii"]
    gol = next(x for x in ab["umbrellas"]["ゴルフ傘"]["rows"] if x["v"] == V_RUN)["ii"]
    dn5 = next(r for r in ab["calm"] if r["v"] == V_RUN)["d_need"]
    a(f"- **走っても0にできるか**: 体の影を覆える直径（下表の『必要な直径』、5m/sで{dn5:.2f}m）に届かなければ0にできない。長傘1.0m・折りたたみ0.9mは足りない。"
      f"ゴルフ傘1.2mも足りず {f0(gol['e'])} 粒（傘なしで走る {f0(ch1_run(res))} の{gol['e'] / ch1_run(res) * 100:.0f}%）。**直径1.4mなら5m/sで {f0(big['e'])} 粒**（手は前へ{cm(big['hand'][0])}・高さ{big['hand'][1]:.2f}m、肩から{big['reach'] * 100:.0f}cmで届く）。"
      "7m/s は必要な直径1.49mで、1.4mでも足りない。")
    a(f"- **腕の届く範囲は効いていない**: 長傘の走り5m/sの最適な手は肩から{rn['reach'] * 100:.0f}cm（腕0.60mの範囲内）。腕を0.4mに縮めても同じ。**腕0（手が肩の位置のまま）のときだけ悪くなる**（感度表）。"
      "『傘を前に出す』が効くのは、傘の中心を体の斜め前上に動かして、傘の影を体に重ねるため。最適な置き方は、傘の直径が体の影を覆える範囲で決まる。")
    a("")
    a("| 速さ | 雨の見かけの角度 θ | 体の影の長さ 1.7·sinθ＋0.25·cosθ | 必要な直径 √(0.45²＋影の長さ²) |\n|---|---|---|---|")
    for r in ab["calm"]:
        t = math.radians(r["ii"]["theta"])
        a(f"| {r['v']:g}m/s | {r['ii']['theta']:.1f}° | {BH * math.sin(t) + BL * math.cos(t):.2f}m | {r['d_need']:.2f}m |")
    a("")
    a("### 傘の大きさ別（無風、(ii)。粒）")
    a("")
    a("| 傘 | 直径 | " + " | ".join(f"{v:g}m/s" for v in V_LIST_BIN) + " |\n|---|---|" + "---|" * len(V_LIST_BIN))
    for nm, u in ab["umbrellas"].items():
        cells = {x["v"]: f0(x["ii"]["e"]) for x in u["rows"]}
        a(f"| {nm} | {u['Du']:g}m | " + " | ".join(cells.get(v, "—") for v in V_LIST_BIN) + " |")
    a("")
    for nm, u in ab["umbrellas"].items():
        for x in u["rows"]:
            if x["v"] in (V_WALK, V_RUN):
                r = x["ii"]
                a(f"- {nm}（{u['Du']:g}m）{x['v']:g}m/s: (i) {f0(x['i']['e'])} → (ii) **{f0(r['e'])}**。手 {cm(r['hand'][0])}／{r['hand'][1]:.2f}m、φ {r['phi']:.1f}°、"
                  f"傘の中心 {cm(r['center'][0])}／{r['center'][1]:.2f}m"
                  + ("" if r['e'] < 0.5 else f"、前の濡れる一番高い所 {cm(r['z_dry_center'])}〜{cm(r['z_dry_edge'])}"))
    a("")
    a("### 風3m/s（長傘、(ii)。粒）")
    a("")
    for key, title in (("tail", "追い風"), ("head", "向かい風")):
        a(f"**{title}**")
        a("")
        a("| 速さ | 傘なし | (i) 最適傾き | (ii) 腕を伸ばす | 手（前へ／高さ） | φ（θ） | 傘の中心（前へ／高さ） |\n|---|---|---|---|---|---|---|")
        for x in ab[key]:
            r = x["ii"]
            a(f"| {x['v']:g}m/s | {f0(x['i']['plain'])} | {f0(x['i']['e'])} | **{f0(r['e'])}** | {cm(r['hand'][0])}／{r['hand'][1]:.2f}m | {r['phi']:.1f}°（{r['theta']:.1f}°） | "
              f"{cm(r['center'][0])}／{r['center'][1]:.2f}m |")
        a("")
    a("（上の表は手が体の前半分だけの版。追い風で雨が後ろから来る速さ〈3m/s未満〉では傘を後ろへ出せない。下の (ii') は手を後ろ半分にも置ける版。）")
    a("")
    wb = ab.get("wind_behind")
    if wb:
        a("### 風3m/s: 手を体の後ろにも置ける (ii')（長傘。追い風で雨が後ろから来るときは傘を後ろへ傾ける・後ろへ出せる。粒）")
        a("")
        for key, title in (("tail", "追い風"), ("head", "向かい風")):
            a(f"**{title} 3m/s**")
            a("")
            a("| 速さ | 傘なし | (i) 最適傾き | (ii) 前だけ | (ii') 後ろも可 | 手（前＋/後ろ−／高さ） | 傾き φ（前＋/後ろ−）（θ） | 傘の中心（前＋/後ろ−／高さ） |\n|---|---|---|---|---|---|---|---|")
            for x in wb[key]:
                r = x["iib"]
                r0 = next(y for y in ab[key] if y["v"] == x["v"])["ii"]
                a(f"| {x['v']:g}m/s | {f0(x['i']['plain'])} | {f0(x['i']['e'])} | {f0(r0['e'])} | **{f0(r['e'])}** | {cm(r['hand'][0])}／{r['hand'][1]:.2f}m | "
                  f"{r['phi']:.1f}°（{r['theta']:.1f}°） | {cm(r['center'][0])}／{r['center'][1]:.2f}m |")
            a("")
        wt = {x["v"]: x["iib"] for x in wb["tail"]}
        wh = {x["v"]: x["iib"] for x in wb["head"]}
        a(f"- **追い風 3m/s（(ii')）**: 歩き 1.4m/s **{f0(wt[V_WALK]['e'])} 粒**、走り 5m/s **{f0(wt[V_RUN]['e'])} 粒** → "
          + ("**どちらも0粒（差なし）**" if wt[V_WALK]['e'] < 0.5 and wt[V_RUN]['e'] < 0.5 else ("歩きのほうが少ない" if wt[V_WALK]['e'] < wt[V_RUN]['e'] else "走りのほうが少ない")) + "。"
          f"歩きは雨が後ろから来る（見かけ {abs(wt[V_WALK]['theta']):.0f}°）ので**後ろへ{abs(wt[V_WALK]['phi']):.0f}°傾ける**、走りは雨が前から来る（{wt[V_RUN]['theta']:.0f}°）ので**前へ{wt[V_RUN]['phi']:.0f}°傾ける**。")
        a(f"- **向かい風 3m/s（(ii')）**: 歩き 1.4m/s **{f0(wh[V_WALK]['e'])} 粒**、走り 5m/s **{f0(wh[V_RUN]['e'])} 粒** → "
          + ("歩きのほうが少ない" if wh[V_WALK]['e'] < wh[V_RUN]['e'] else "走りのほうが少ない") + f"（差 {f0(abs(wh[V_WALK]['e'] - wh[V_RUN]['e']))} 粒、約{abs(wh[V_WALK]['e'] - wh[V_RUN]['e']) / max(wh[V_WALK]['e'], wh[V_RUN]['e']) * 100:.0f}%。ほぼ同じ）。"
          f"雨は前から来る（歩き{wh[V_WALK]['theta']:.0f}°・走り{wh[V_RUN]['theta']:.0f}°）ので、どちらも**前へ傾ける**（歩き{wh[V_WALK]['phi']:.0f}°、走り{wh[V_RUN]['phi']:.0f}°）。")
        a("")
    a("### 感度（長傘、(ii)。粒。基準: 腕0.60m・肩1.45m・柄0.65m・余裕10cm）")
    a("")
    a("| 変えたもの | 値 | 歩き 1.4m/s | 走り 5m/s |\n|---|---|---|---|")
    a(f"| 基準 | — | {f0(ab['sens_base']['walk']['e'])} | {f0(ab['sens_base']['run']['e'])} |")
    for s_ in ab["sens"]:
        a(f"| {s_['label']} | {s_['value']:g}m | {f0(s_['walk']['e'])} | {f0(s_['run']['e'])} |")
    a("")


def ch1_run(res):
    return res["ch1"]["run_plain"]


# ============================================================
# 5. 数字の書き出し
# ============================================================
SOURCES = [
    ("親骨60cmの長傘の開いた直径", "約101〜107cm（商品表: mabu 103、小川 102、Wpc. 107、estaa 101 ほか）→ 長傘 直径 1.0m を採用",
     "https://my-best.com/21654（マイベスト「60cmの傘のおすすめ人気ランキング」の商品表。WebFetch で確認）"),
    ("親骨55cm（折りたたみ）の直径", "約97cm（無印良品 晴雨兼用 2通りにたためる折りたたみ傘 親骨55cm）。親骨50cmで約80〜90cm、親骨60cmの折りたたみで約108cm → 折りたたみ 直径 0.9m を採用",
     "https://www.muji.com/jp/ja/store/cmdty/detail/4550584128011 ほか（WebSearch の要約で確認。ページ本体の取得はタイムアウト）"),
    ("親骨65cm・70cmのゴルフ傘の直径", "親骨65cmで約110〜115cm、70cmで約120〜125cm → ゴルフ傘 直径 1.2m（親骨70cm級）を採用",
     "https://my-best.com/21652 ／ https://osusume.mynavi.jp/2921（WebSearch の要約で確認。mynavi のページ本体は 404）"),
    ("親骨と直径の関係", "親骨にはカーブがあり、直径は親骨のおよそ1.7〜1.8倍", "同上（WebSearch の要約）"),
    ("持つ高さ（円板の高さ）", "**調べても分からなかった**（頭から傘までの距離を載せた情報源が見つからない）→ **仮の値 1.9m**。"
     "根拠は推定のみ: 長傘は閉じて全長約85〜87cm（マイベスト・無印の商品表）、手は柄の端に近い高さ（身長1.7mなら約1.2〜1.3m）→ てっぺん約1.95〜2.0m、縁（椀の下端）はそれより10〜20cm低い。円板をその間の1.9mに置く（構成案の試算と同じ）",
     "（推定。出典なし）"),
]


def write_numbers(res):
    ch1, ch2, ch3, ch4, ch5, ch6, pe, brk = (res[k] for k in ("ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "people", "breakdown_mc"))
    L = []
    a = L.append
    f0 = lambda x: f"{x:,.0f}"
    a("# 雨ロング（傘をさしたら、走ると濡れる？）数字一覧")
    a("")
    a(f"自動生成（sims/ame-long.py --numbers）。**手で編集しない。** 計算 {res['elapsed']:.0f}秒。")
    a("雨・体・動きはショート（sims/ame-hashiru.py）と同じ: 1時間10mm、粒は直径2mm・秒速6.49m、数密度 約102個/m³、体は幅0.45×奥行き0.25×高さ1.7mの直方体、道のり100m。")
    a(f"傘 = 円板（直径 Du、体の真上、高さ Hu）。基本の傘は**長傘 Du={DU:g}m・Hu={HU:g}m**。")
    a("")
    a("## 使い方の注意（台本・絵の担当へ）")
    a("")
    a("- **表の数字は (a) 期待値（細かい格子で数値積分、速さをぴったり指定）**。乱数のばらつきを含まないので、台本の数字はこれを使う。")
    a("- **1万人の分布・速さごとの平均は (b)（雨粒を実際にまく）**。画面の散布図はここから（out/ame-long/data.npz に1万人ぶんの速さと粒数）。")
    a("- (a) と (b) の一致は --check で確認（件数は末尾）。")
    a(f"- **構成案の試算（歩き約740粒）は、体の中心線で濡れる高さ（足元16cm）に幅を掛けた近似（n×幅×T×|c|×0.16m ≒ {NDENS * BW * (D / V_WALK) * V_WALK * 0.16:.0f}粒）。"
      f"3次元で数えると歩きは約{ch1['walk_umb']:,.0f}粒。** 傘の影は体の左右の端で短く、端では40cmの高さまで濡れるため（2章）。走りは構成案どおり約{ch1['run_umb']:,.0f}粒（構成案6,500）。")
    a("- **『傘の直径1.0m』は崖の上にいる**: 直径0.9mで歩き約2,200粒、1.1mで約140粒、1.2mで0粒（4章）。歩きの数字は寸法に強く依存する。")
    a("")
    a("## 傘の寸法の出典（WebSearch、2026-10-11）")
    a("")
    for k, v, u in SOURCES:
        a(f"- **{k}**: {v}")
        a(f"  - 出典: {u}")
    a("- 採用: 長傘 (1.0m, 1.9m)／折りたたみ傘 (0.9m, 1.9m)／ゴルフ傘 (1.2m, 1.9m)。**折りたたみ・ゴルフの高さも1.9mにそろえた**（大きさだけを変えて比べるため。高さの影響は4章の感度で別に見る）。")
    a("- 本物の傘は椀形で、縁が頂点より低い。円板は縁と頂点の間を代表させた近似（円板が実際より高ければ濡れる粒が増え、低ければ減る → 感度は4章）。")
    a("")
    a("## 1章: 傘あり・無風・水平")
    a("")
    a(f"| 速さ | 傘なし | 傘あり | 傘ありは傘なしの |\n|---|---|---|---|")
    for r in ch1["rows"]:
        a(f"| {r['v']:g} m/s（時速{r['v'] * 3.6:.1f}km） | {f0(r['plain'])} | {f0(r['umb'])} | {r['ratio'] * 100:.0f}% |")
    a("")
    a(f"- 傘なし: 歩き {f0(ch1['walk_plain'])} 粒 → 走り {f0(ch1['run_plain'])} 粒。走ると **{ch1['cut_plain'] * 100:.1f}%減（約3割減）**。")
    a(f"- 傘あり（水平）: 歩き **{f0(ch1['walk_umb'])} 粒** → 走り **{f0(ch1['run_umb'])} 粒**。**走ると {ch1['run_over_walk_umb']:.1f} 倍（約6倍）濡れる**（構成案の見込みは約9倍）。")
    a(f"- 傘ありで歩く {f0(ch1['walk_umb'])} は、傘なしで歩く {f0(ch1['walk_plain'])} の {ch1['umb_vs_plain_walk'] * 100:.1f}%（約{1 / ch1['umb_vs_plain_walk']:.0f}分の1）。"
      f"傘ありで走る {f0(ch1['run_umb'])} は、傘なしで走る {f0(ch1['run_plain'])} の {ch1['umb_vs_plain_run'] * 100:.0f}%。")
    a(f"- **傘ありは遅いほどよい**。秒速 **{ch1['zero'][0][1]:.2f}m（時速{ch1['zero'][0][1] * 3.6:.1f}km）以下ではほぼ0粒**（期待値1粒未満）。それより速くなるほど増え続ける（単調増加）。1〜7m/s で一番少ないのは 1.0m/s の 0粒。")
    a("  - 傘なしは逆に速いほど減る（ショート）。傘ありだけが逆転して『遅いほどよい』。")
    a("- 1万人（速さ1〜7m/s一様、雨粒をまく (b)）の速さごとの平均（±0.1m/s の人たち）:")
    a("")
    a("| 速さ | 傘なし (b) | 傘あり水平 (b) | （参考）傘あり水平 (a) ぴったりの速さ | 傘あり 最適な傾き (b) |\n|---|---|---|---|---|")
    for c in V_LIST_BIN:
        k = f"{c}"
        a(f"| {c:g} m/s | {f0(pe['plain_calm']['bins'][k]['mean'])} | {f0(pe['flat_calm']['bins'][k]['mean'])} | "
          f"{f0(expected(c, 0.0, DU, HU, 0.0))} | {f0(pe['opt_calm']['bins'][k]['mean'])} |")
    a("")
    a(f"  - 1万人全体の平均: 傘なし {f0(pe['plain_calm']['mean'])}、傘水平 {f0(pe['flat_calm']['mean'])}、傘最適傾き {f0(pe['opt_calm']['mean'])}。"
      f"傘水平で0粒の人は {pe['flat_calm']['zero_frac'] * 100:.1f}%（秒速1.11m以下の人）。1万人の最大: 傘なし {pe['plain_calm']['maximum']:,}、傘水平 {pe['flat_calm']['maximum']:,}。")
    a("  - (b) の平均が (a) とずれて見えるのは、±0.1m/s の人たちの平均が『ぴったりの速さ』より少し高くなる（曲線が下に凸）ため。台本の数字は (a) の列を使う。")
    a("")
    a("## 2章: どこに当たるか")
    a("")
    a("雨粒には横向きの速さがないので、**体の横の面には当たらない（横 = 0粒）**。当たるのは上の面と、前（c<0）の面だけ（無風で進むとき、後ろの面には当たらない）。")
    a("")
    a("| | 上 | 前 | 横 | 計 | 前の面の濡れる面積 |\n|---|---|---|---|---|---|")
    for v in (V_WALK, V_RUN):
        for tag, nm in (("plain", "傘なし"), ("umb", "傘あり水平")):
            d = ch2[f"{v}"][tag]
            a(f"| {v:g}m/s {nm} | {f0(d['top'])} | {f0(d['face'])} | 0 | {f0(d['total'])} | {d['face_wet_frac'] * 100:.0f}% |")
    a("")
    a("前の面に当たる高さ別（粒。傘あり水平）:")
    a("")
    a("| 高さ | 歩き 1.4m/s | 走り 5m/s |\n|---|---|---|")
    for k in ("0.0-0.5", "0.5-1.0", "1.0-1.5", "1.5-1.7"):
        a(f"| {k.replace('-', '〜')}m | {f0(ch2['1.4']['umb']['bands'][k])} | {f0(ch2['5.0']['umb']['bands'][k])} |")
    a("")
    dw, dr = ch2["1.4"]["umb"], ch2["5.0"]["umb"]
    a(f"- **傘あり・歩き 1.4m/s**: 上は0粒（傘が全部防ぐ）。前は **足元 {dw['z_dry_center'] * 100:.0f}cm より下**（体の中心線）だけ濡れる。体の左右の端では {dw['z_dry_edge'] * 100:.0f}cm より下まで濡れる（傘の影が端で短いため）。前の面の濡れる面積は {dw['face_wet_frac'] * 100:.0f}%。")
    a(f"- **傘あり・走り 5m/s**: 上は0粒。前は **{dr['z_dry_center'] * 100:.0f}cm（中心線）〜{dr['z_dry_edge'] * 100:.0f}cm（端）より下が全部濡れる**（脚から胸まで。頭と肩だけ乾く）。前の面の濡れる面積は {dr['face_wet_frac'] * 100:.0f}%。")
    pw, pr_ = ch2["1.4"]["plain"], ch2["5.0"]["plain"]
    a(f"- 傘なしは、上と前の全部が濡れる（前の面の濡れる面積100%）。歩きは上 {f0(pw['top'])} + 前 {f0(pw['face'])}、走りは上 {f0(pr_['top'])} + 前 {f0(pr_['face'])}（前は速さによらず同じ。ショートと同じ）。")
    a(f"- 雨粒をまく数え方 (b)（400人の平均）の内訳: 歩き 前 {brk['walk']['face']:.0f}・上 {brk['walk']['top']:.0f}、走り 前 {brk['run']['face']:.0f}・上 {brk['run']['top']:.0f}（(a) と一致）。")
    a("")
    a("## 3章: 前に傾けたら")
    a("")
    a("**一番濡れない傾きは、雨の見かけの角度 atan(v/6.49) にぴったり一致する**（傘を雨に垂直に向ける）。傘の中心が体の真上に固定なら、雨の向きに沿って体へ落ちる傘の影は、どの傾きでも同じ中心の楕円で、"
      "雨に垂直のときだけ円（最大）になり、ほかの傾きの影はその内側に収まる。だから垂直が必ず最良（格子の探索でも確かめた）。")
    a("")
    a("| 速さ | 雨の見かけの角度 atan(v/6.49) | 最適な傾き φ* | 水平のとき | φ* のとき | 減った割合 | φ* で前が濡れる高さ（中心線〜端） |\n|---|---|---|---|---|---|---|")
    for r in ch3["rows"]:
        a(f"| {r['v']:g}m/s | {r['apparent']:.1f}° | **{r['phi']:.1f}°** | {f0(r['e0'])} | **{f0(r['e'])}** | {(1 - r['e'] / r['e0']) * 100 if r['e0'] > 0 else 0:.0f}% | "
          f"{('0（濡れない）' if r['e'] <= 0 else f'{r['z_dry_center'] * 100:.0f}〜{r['z_dry_edge'] * 100:.0f}cm より下')} |")
    a("")
    r14 = next(r for r in ch3["rows"] if r["v"] == 1.4)
    r5 = next(r for r in ch3["rows"] if r["v"] == 5.0)
    a(f"- **歩き 1.4m/s**: 傾き {r14['phi']:.1f}°（見かけの角度 {r14['apparent']:.1f}°）で {f0(r14['e0'])} → **{f0(r14['e'])} 粒**（{(1 - r14['e'] / r14['e0']) * 100:.0f}%減）。0にはならない: 直径1.0mの傘は"
      f"体の左右の端×足元の角までは覆えない（2章）。")
    a(f"- **走り 5m/s**: 傾き {r5['phi']:.1f}°（見かけの角度 {r5['apparent']:.1f}°）で {f0(r5['e0'])} → **{f0(r5['e'])} 粒**（{(1 - r5['e'] / r5['e0']) * 100:.0f}%減）。"
      f"**傾けても足は濡れる**: 前は {r5['z_dry_center'] * 100:.0f}〜{r5['z_dry_edge'] * 100:.0f}cm より下が全部濡れる（前の面の{r5['face_wet_frac'] * 100:.0f}%）。")
    a(f"- 傾けた傘で走ると {f0(r5['e'])}、歩くと {f0(r14['e'])} → **{r5['e'] / r14['e']:.1f} 倍**（水平のとき {ch1['run_over_walk_umb']:.1f} 倍）。傾けても逆転は解消しない。")
    a(f"- 傾けた傘で走る {f0(r5['e'])} は、傘なしで走る {f0(ch1['run_plain'])} の {r5['e'] / ch1['run_plain'] * 100:.0f}%。")
    a(f"- 傾き φ の掃引（歩き・走り、φ=0〜50°）は data.json の ch3.phi_curve に1度刻みで入っている（傘のダイヤルの絵用）。")
    a("")
    a("(b) の検算: 1万人が各自の速さの φ* で傘を傾けたとき（雨粒をまく）の速さごとの平均は 1章の表の最右列。")
    a("")
    a("## 4章: 傘の大きさ")
    a("")
    a("| 傘 | 直径 | 歩き 水平 | 歩き 最適傾き | 走り 水平 | 走り 最適傾き | 走り÷歩き（水平） | 1粒未満になる最大の速さ |\n|---|---|---|---|---|---|---|---|")
    a(f"| 傘なし | — | {f0(ch1['walk_plain'])} | {f0(ch1['walk_plain'])} | {f0(ch1['run_plain'])} | {f0(ch1['run_plain'])} | {ch1['run_plain'] / ch1['walk_plain']:.2f}倍 | — |")
    for name, e in ch4["umbrellas"].items():
        w_, r_ = e["walk"], e["run"]
        ratio = (r_["flat"] / w_["flat"]) if w_["flat"] > 0 else None
        a(f"| {name} | {e['Du']:g}m | {f0(w_['flat'])} | {f0(w_['opt'])}（{w_['phi']:.1f}°） | {f0(r_['flat'])} | {f0(r_['opt'])}（{r_['phi']:.1f}°） | "
          f"{('—（歩きが0）' if ratio is None else f'{ratio:.1f}倍')} | {e['zero'][0][1]:.2f}m/s |")
    a("")
    a("直径の掃引（高さ 1.9m、粒）:")
    a("")
    a("| 直径 | 歩き 水平 | 歩き 最適 | 走り 水平 | 走り 最適 |\n|---|---|---|---|---|")
    for r in ch4["du_sweep"]:
        a(f"| {r['Du']:g}m | {f0(r['walk']['flat'])} | {f0(r['walk']['opt'])} | {f0(r['run']['flat'])} | {f0(r['run']['opt'])} |")
    a("")
    a("持つ高さの感度（長傘 1.0m、粒）:")
    a("")
    a("| 高さ | 歩き 水平 | 歩き 最適 | 走り 水平 | 走り 最適 |\n|---|---|---|---|---|")
    for r in ch4["hu_sweep"]:
        a(f"| {r['Hu']:g}m | {f0(r['walk']['flat'])} | {f0(r['walk']['opt'])} | {f0(r['run']['flat'])} | {f0(r['run']['opt'])} |")
    a("")
    du_ = {r["Du"]: r for r in ch4["du_sweep"]}
    hu_ = {r["Hu"]: r for r in ch4["hu_sweep"]}
    a(f"- 傘が大きいほど歩きが急に減る（直径1.2mで{f0(du_[1.2]['walk']['flat'])}粒）。一方、**走りは傘が大きくなっても大して減らない**"
      f"（直径1.0m→1.2mで歩き {f0(du_[1.0]['walk']['flat'])}→{f0(du_[1.2]['walk']['flat'])} なのに、走りは {f0(du_[1.0]['run']['flat'])}→{f0(du_[1.2]['run']['flat'])}）。"
      "→ 大きい傘ほど『歩く』の価値が上がり、歩きと走りの差が**広がる**（縮まらない）。")
    a(f"- **歩きの数字は傘の寸法に非常に敏感**: 直径が±10cm（0.9〜1.1m）で歩きは {f0(du_[0.9]['walk']['flat'])}〜{f0(du_[1.1]['walk']['flat'])} 粒、"
      f"高さが±10cmで {f0(hu_[1.8]['walk']['flat'])}〜{f0(hu_[2.0]['walk']['flat'])} 粒。走りは直径±10cmで {f0(du_[0.9]['run']['flat'])}〜{f0(du_[1.1]['run']['flat'])}、"
      f"高さ±10cmで {f0(hu_[1.8]['run']['flat'])}〜{f0(hu_[2.0]['run']['flat'])} と鈍感。")
    a("")
    if "ch4b" in res:
        write_arm_section(a, f0, res)
    a("## 5章: 風（雨粒が水平に秒速3mで流れる。ショートと同じ扱い）")
    a("")
    for key, title in (("tail", "追い風 3m/s（雨は進む向きに流れる）"), ("head", "向かい風 3m/s（雨は進む向きと逆に流れる）")):
        g = ch5[key]
        a(f"### {title}")
        a("")
        a("| 速さ | 雨の見かけの角度 | 傘なし | 傘水平 | 最適な傾き φ* | 傘最適傾き |\n|---|---|---|---|---|---|")
        for r in g["rows"]:
            a(f"| {r['v']:g}m/s | {r['apparent']:.1f}° | {f0(r['plain'])} | {f0(r['flat'])} | {r['phi']:.1f}° | {f0(r['opt'])} |")
        a("")
    gt = ch5["tail"]
    a("（φ* は前へ傾ける向きが＋、後ろへ傾けるのが−。追い風で自分より雨が速い（歩きが風より遅い）と雨は後ろから来るので後ろへ傾ける。上限は±55°）")
    a("")
    a(f"- **追い風で風と同じ秒速3mで歩く**: 傘なし {f0(ch5['tail_match']['plain'])} 粒（ショートの谷）→ **傘水平で {f0(ch5['tail_match']['flat'])} 粒（完全に0）**。雨が真上から来るので傘が全部防ぐ。")
    a(f"- 傘水平で0粒になる速さの範囲（追い風3m/s）: **秒速 {gt['zero_flat'][0][0]:.2f}〜{gt['zero_flat'][0][1]:.2f}m（時速{gt['zero_flat'][0][0] * 3.6:.1f}〜{gt['zero_flat'][0][1] * 3.6:.1f}km）**。"
      f"風と同じ速さの前後に幅がある（雨の見かけの角度が小さいとき、傘が体を覆える）。無風の0粒の範囲は 〜{ch1['zero'][0][1]:.2f}m/s。")
    a(f"- 追い風・傘水平で 1万人 の平均: {f0(pe['flat_tail']['mean'])} 粒（傘なし追い風 {f0(pe['plain_tail']['mean'])}）。向かい風・傘水平 {f0(pe['flat_head']['mean'])}（傘最適傾き {f0(pe['opt_head']['mean'])}）。")
    a("- **向かい風では歩いても雨が前から来る**: 傘水平で 1.4m/s が " + f0(ch5['head']['rows'][1]['flat']) + " 粒、最適に前へ傾けて " + f0(ch5['head']['rows'][1]['opt']) + " 粒（傘なし " + f0(ch5['head']['rows'][1]['plain']) + "）。"
      "秒速1mでも傘水平は " + f0(ch5['head']['rows'][0]['flat']) + " 粒。向かい風は歩いても走っても傘ではほとんど防げない。")
    a(f"- 追い風・傘水平で走ると（5m/s）{f0(gt['rows'][5]['flat'])} 粒、7m/s で {f0(gt['rows'][6]['flat'])} 粒。風より速く走ると雨が前から来て、傘の効きが落ちる。")
    a("")
    a("## 6章: まとめ用の数字")
    a("")
    a(f"- **傘なしなら走る**: 歩き {f0(ch6['plain_walk'])} → 走り {f0(ch6['plain_run'])}（**約3割減**、{ch6['plain_cut'] * 100:.1f}%減）。")
    a(f"- **傘ありなら歩く**: 水平で 歩き {f0(ch6['umb_walk'])} ／ 走り {f0(ch6['umb_run'])}（走ると **{ch6['umb_ratio']:.1f} 倍**）。前へ傾けて 歩き {f0(ch6['umb_opt_walk'])}（{ch6['umb_opt_phi_walk']:.0f}°）／ 走り {f0(ch6['umb_opt_run'])}"
      f"（{ch6['umb_opt_phi_run']:.0f}°）（**{ch6['opt_ratio']:.1f} 倍**）。")
    a(f"- 傘をさして歩く（水平）は、傘なしで走るより少ない: {f0(ch6['umb_walk'])} は {f0(ch6['plain_run'])} の {ch6['walk_umb_vs_plain_run'] * 100:.0f}%。前へ傾けると {ch6['walk_opt_vs_plain_run'] * 100:.0f}%。")
    a(f"- 傘をさして走る（水平）{f0(ch6['umb_run'])} は、傘なしで走る {f0(ch6['plain_run'])} の {ch6['run_umb_vs_plain_run'] * 100:.0f}%、傘なしで歩く {f0(ch6['plain_walk'])} の {ch6['run_umb_vs_plain_walk'] * 100:.0f}%。傾けると {ch6['run_opt_vs_plain_run'] * 100:.0f}%（対 傘なしで走る）。")
    a("- 答えは『傘を持っているか』で逆になる: 傘なし → 走るほうが少ない（約3割減）／傘あり → 歩くほうが少ない（約6倍の差。水平）。")
    a("- 条件: 傘は体の真上・直径1.0m・高さ1.9m（仮）。風があると変わる（5章）: 追い風と同じ速さで歩けば0粒、向かい風は傘でもほとんど防げない。")
    a("")
    a("## モデルの置き方・限界")
    a("")
    a("- 傘は円板（椀形でない）。柄・手・腕は無視。傘の中心は体の真上で固定（持つ手の位置で傘をずらす動きは考えない）。")
    a("- 歩き出す前から傘をさしている（定常状態）。歩き出した瞬間の『傘の下の雨粒』は数えない。")
    a("- 雨粒は全部2mm、風は水平一定、乱れなし。人は直方体（頭と肩の凹凸なし）。")
    a("- 傾きの探索範囲は±55°（これ以上は円板が頭にぶつかる）。向かい風で速く走る（見かけの角度55°超）と、最適な傾きに届かない。")
    a("- **傘の寸法（特に持つ高さ 1.9m）は仮**。歩きの数字は直径・高さの10cmで大きく動く。")
    a("")
    a(f"## 照合: {res.get('n_checks', '—')} 件 すべて OK（check_answers）")
    a("")
    a("- A 傘なしでショートの式・数字と一致（式との差0、歩き13,100・走り9,300・底7,800・追い風の谷2,500／2,600、約3割減）")
    a("- B 傘の影の幾何（真上から降る→0粒、止まっている→0粒、影の下端高さが解析式に一致、左右鏡映、巨大傘→0、直径が大きいほど減る、格子4mmと2mmで同じ、最適な傾き=雨に垂直を格子探索と照合）")
    a("- C 期待値 (a) と雨粒をまく (b) の一致（400人×18条件: 傘あり・傾きあり・風あり・折りたたみ/ゴルフ・高さ1.8m・追い風・向かい風・傘なし。上/前と高さ別の内訳も）")
    a("- D 1万人×8条件（傘なし/傘水平/傘最適傾き×無風、追い風・向かい風）が、人ごとの期待値＋ポアソンのばらつきに一致（平均0・分散1）。速さごとの平均も一致")
    fence_txt = []
    for nm, c, ex, rx in res.get("fences", []):
        fence_txt.append(f"{nm} {c:g}m/s（期待値 {ex:,.0f} → 『約{rx:,.0f}』）")
    if fence_txt:
        a("- 丸めの境目に近い数字（100粒単位。1万人の平均の標準誤差の3倍以内に境目がある）: " + "、".join(fence_txt) +
          "。別の乱数の1万人の平均だと隣の100に見えることがある → **画面に出す数字は (a) の期待値から丸める**。")
    a("- E 画面に出す数字（100粒単位の丸め、『約○割減』『約○倍』）が、別の乱数の1万人（速さも別）でも同じ")
    a("- F 答えの形（傘なしは走る、傘ありは歩く、など）")
    if "ch4b" in res:
        a("- G 腕を伸ばす版 (ii)（(i) との一致、届かない・体の後ろ・めり込む置き方は選ばれない、雨粒をまいた平均との一致、腕・傘が大きいほど減る、0粒になれる直径の下限、など）")
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "numbers.md"
    f.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("書き出し:", f)


# ============================================================
# モデルの CLI（--check / --numbers / --recompute）。場面の CLI（--stills など）はファイルの最後
#   2026-10-11 場面を足すときに、ここを「モデルの引数があるときだけ」にした（中身は元のまま）
# ============================================================
_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers", "--recompute"))
if __name__ == "__main__" and _MODEL_CLI:
    args = sys.argv[1:]
    res = load(recompute="--recompute" in args)
    if "--numbers" not in args:
        res["n_checks"] = check(res)
    if "--check" not in args:
        if "n_checks" not in res:
            res["n_checks"] = check(res)
        write_numbers(res)
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・音・CLI）。2026-10-11 追加。絵コンテ: research/ame_long_storyboard.md
# モデル部分（上）は変えない。人・雨の線・当たった粒の点・散布図・雨音はショート sims/ame-hashiru.py からコピーして、
# 横型の見開きの左ページに合わせて直した（ショート側は触らない）。
# 傘（円板の断面）・傘の影・雨の見かけの傾き・傾けるダイヤル・雨の向きから見た図は、ここで新しく描いた。
# ####################################################################################################
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, rrect, shimmer, text,
                         text_width, thump, tick, whoosh, riser, beat, _t, SR)
from engine.note import INK, PENCIL, RED, PAPER, pen_circle, pen_line, sticky
from engine.voice import split_reading

lf.use()
RES = load()                                         # data.json（モデルの結果。画面の数字はすべてここから）
VOICE_DIR = OUT / "voice"
_WORKER = __name__ != "__main__"                     # 並列計算の子プロセス（__mp_main__）など。場面は作るが合成はしない
LX0_, LY0_, LX1_, LY1_ = lf.LEFT
RX = 1050                                            # 右ページの書き出しの x


def fmt(n):
    return f"{int(round(n)):,}"


def r100(x):
    """画面に出す丸め（100粒単位）。numbers.md の (a) 期待値から"""
    return int(round(float(x) / 100.0)) * 100


# ============================================================
# 台本 → 時間割（ナレーションの文言は publish/ame-long/script.md v1 のまま。読みの指定 {表記|よみ} だけ足した。
# 字幕が2行に収まらない文・数字を出す所で区切りたい文は、文言を変えずに2つの Line に分けた）
# ============================================================
CH_TITLES = ["雨の中を100m", "傘をさして100m", "なぜ？", "では、傘を前に傾けたら？", "では、傘の大きさを変えたら？",
             "では、風が吹いたら？", "まとめ"]
CARD_TEXT = {6: "どっちが濡れない？"}                 # 章の付箋の字（チャプター名と違うもの）
(CH_OPEN, CH_UMB, CH_WHY, CH_TILT, CH_SIZE, CH_WIND, CH_END) = range(7)
SPEED = 1.0                                          # 声の速さ（合戦ロングと同じ）
FAKE = "--fake-voice" in sys.argv                    # AivisSpeech なしで長さを見積もる確認用（無音）。本番では使わない


def _items():
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        L("c0_1", "傘をさして、雨の中を{100m|ひゃくメートル}。歩く人と走る人、どちらが濡れないでしょう。", pause=0.5),
        L("c0_2", "雨は、{1時間|いちじかん}に{10mm|じゅうミリ}。傘がいる強さです。", pause=0.4),
        L("c0_3", "{雨粒|あまつぶ}は直径{2mm|二ミリ}。{秒速6.5m|秒速六点五メートル}で、まっすぐ落ちてくるとします。", pause=0.4),
        L("c0_4", "左の人は歩きます。{秒速1.4m|秒速一点四メートル}、{時速5km|時速五キロ}です。", pause=0.3),
        L("c0_5", "右の人は走ります。{秒速5m|秒速五メートル}、{時速18km|時速十八キロ}。", pause=0.4),
        L("c0_6", "比べる物差しとして、まず傘なしで。", pause=0.1),
        G("g0", 4.3),
        L("c0_7", "体に当たった雨粒は、歩くと{約13,100粒|約一万三千百粒}。走ると{約9,300粒|約九千三百粒}。", pause=0.3),
        L("c0_7b", "走ると、{約3割|約三割}減りました。", pause=0.8),
        L("c0_8", "では、傘をさしたら？", pause=0.7),
        L("c1_1", "傘は、直径{1m|一メートル}。まずは、体の真上にまっすぐ、頭より少し上の高さ{1.9m|いってんきゅうメートル}で持つとします。", pause=0.4),
        L("c1_2", "上からの雨は、傘が防ぐ。あとは、雨の中にいる時間が短いほうが得。", pause=0.3),
        L("c1_3", "だから、傘があっても、走るほうが濡れない。そう思えます。", pause=0.4),
        L("c1_4", "確かめてみます。", pause=1.1),       # 言い終わってから章カードまで約0.5秒の間（台本の指定）
        C(CH_TITLES[1], id="ch1", gap=1.4),
        L("c2_1", "傘をさして、{100m|ひゃくメートル}。", pause=0.1),
        G("g2", 7.4),
        L("c2_2", "歩いた人は、{約1,100粒|約千百粒}。", pause=0.4),
        L("c2_3", "走った人は、{約6,600粒|約六千六百粒}。", pause=1.4),   # 2つ目の数字を出して止める
        L("c2_4", "傘があると、走ったほうが、{約6倍|約六倍}濡れました。逆転です。", pause=0.5),
        L("c2_5", "傘をさして歩いた{約1,100粒|約千百粒}は、傘なしで走った{約9,300粒|約九千三百粒}の、{1割|いちわり}ちょっとです。", pause=0.5),
        L("c2_6", "この2つの速さだけの話かもしれないので、{1万人|一万人}に、", pause=0.1),
        L("c2_6b", "{時速3.6km|時速三点六キロ}から{25km|二十五キロ}のいろいろな速さで進んでもらいます。", pause=0.1),
        G("g2b", 6.2),
        L("c2_7", "傘なしは、速いほど減る。傘ありは、速いほど増える。向きが逆です。", pause=0.4),
        L("c2_8", "傘ありで一番濡れなかったのは、一番ゆっくりの人。", pause=0.2),
        L("c2_8b", "{時速4km|時速四キロ}以下なら、ほぼ{0粒|ゼロ粒}でした。", pause=0.85),
        C(CH_TITLES[2], id="ch2", gap=1.2),
        L("c3_1", "なぜでしょう。走る人の目線で見てみます。", pause=0.4),
        L("c3_2", "止まっていれば、雨は上から落ち、傘が雨をさえぎる影が、体を全部覆います。", pause=0.5),
        L("c3_3", "前に進むと、雨は前から斜めに降ってくるように見えます。", pause=0.2),
        L("c3_3b", "自分が進んだぶん、雨が向かってくるからです。", pause=0.4),
        L("c3_4", "歩く速さだと、雨の傾きは{約12度|ヤクジュウニド}。走ると{約38度|約三十八度}。", pause=0.5),
        L("c3_5", "雨が斜めになると、傘の影は、後ろへずれます。", pause=0.7),
        L("c3_6", "影からはみ出した体の前に、雨が当たります。", pause=0.4),
        L("c3_7", "歩く人がはみ出すのは、足元だけ。濡れるのは、地面から{40cm|四十センチ}までです。", pause=0.4),
        L("c3_8", "走る人は、地面から{約140cm|約百四十センチ}まで、はみ出します。", pause=0.2),
        L("c3_8b", "脚から胸まで。乾いているのは、頭と肩だけです。", pause=0.85),
        L("c3_9a", "比べるために、傘なしの粒を、上からと前からに分けます。", pause=0.2),
        L("c3_9", "前から当たる雨は、歩いても走っても同じ、{約7,800粒|約七千八百粒}でした。", pause=0.2),
        L("c3_9b", "速いほど前から来る雨は増えますが、浴びる時間は短くなる。ちょうど打ち消し合うからです。", pause=0.3),
        L("c3_10", "傘ありでは、速いほど体が影からはみ出して、前から当たる雨が増えます。", pause=0.2),
        L("c3_10b", "これが、逆転の理由です。", pause=0.8),
        C(CH_TITLES[3], id="ch3", gap=1.2),
        L("c4_1", "では、傘を前に傾けたら？", pause=0.4),
        L("c4_2", "傾けるとき、傘は少し前に出しますよね。", pause=0.3),
        L("c4_2b", "腕の届く範囲で、傘の位置と傾きをいろいろ試して、一番濡れない持ち方を探します。", pause=0.4),
        L("c4_3", "一番効く傾きは、雨にまっすぐ向ける角度。雨の傾きと、ぴったり同じでした。", pause=0.4),
        L("c4_4", "歩く人は、{12度|十二度}傾けて、傘を少し前へ。{0粒|ゼロつぶ}になりました。", pause=0.85),
        L("c4_5", "走る人は、{38度|三十八度}。傘を、体の{70cm|七十センチ}前まで突き出します。", pause=0.4),
        L("c4_6", "{約6,600粒|約六千六百粒}が、{約2,000粒|約二千粒}。{3分の1|さんぶんのいち}以下です。", pause=0.85),
        L("c4_7", "それでも、{0|ゼロ}にはなりません。地面から{30cm|三十センチ}くらいまで、足元が濡れます。", pause=0.4),
        L("c4_8", "雨の来る方向から見ると、縦に長い体は、直径{1m|一メートル}の傘の円に収まりきらないからです。", pause=0.4),
        L("c4_9", "前に出して傾けても、歩くほうが濡れません。", pause=0.2),
        L("c4_9b", "走って{0|ゼロ}にするには、直径{1m30cm|一メートル三十センチ}より大きい傘が要ります。", pause=0.8),
        C(CH_TITLES[4], id="ch4", gap=1.2),
        L("c5_1", "傘はまっすぐ持ったまま、大きさを変えてみます。", pause=0.3),
        L("c5_2", "直径{90cm|九十センチ}の折りたたみ傘。歩くと{約2,200粒|約二千二百粒}。走ると{約6,900粒|約六千九百粒}。", pause=0.4),
        L("c5_3", "直径{1m20cm|一メートル二十センチ}の大きな傘。歩くと、{0粒|ゼロ粒}。走ると、{約6,000粒|約六千粒}。", pause=0.85),
        L("c5_4", "歩く人は、傘が{10cm|十センチ}大きくなるごとに、ぐっと減ります。", pause=0.2),
        L("c5_4b", "はみ出しが足元だけなので、少し大きくすれば覆えます。", pause=0.3),
        L("c5_5", "走る人は、ほとんど減りません。胸まではみ出しているので、{10cm|十センチ}や{20cm|二十センチ}では足りません。", pause=0.4),
        L("c5_6", "傘が大きいほど、歩くと走るの差は、広がります。", pause=0.4),
        L("c5_7", "傘が十分に大きければ、歩きは、ほぼ{0|ゼロ}。", pause=0.3),
        L("c5_7b", "まっすぐ持つなら、走る人の濡れは、傘の大きさより、速さで決まります。", pause=0.8),
        C(CH_TITLES[5], id="ch5", gap=1.2),
        L("c6_1", "では、風が吹いたら？", pause=0.3),
        L("c6_2", "風は{秒速3m|秒速三メートル}。{雨粒|あまつぶ}も、落ちながら横に{秒速3m|秒速三メートル}で流れるとします。", pause=0.4),
        L("c6_3", "まず、傘をまっすぐ持ったまま。", pause=0.3),
        L("c6_4", "追い風だと、歩くと{約2,400粒|約二千四百粒}、走ると{約1,400粒|約千四百粒}。", pause=0.6),
        L("c6_5", "向かい風は、雨が正面から吹きつけるので、数字がぐっと大きくなります。", pause=0.3),
        L("c6_5n", "歩くと{約19,800粒|約一万九千八百粒}、走ると{約11,800粒|約一万千八百粒}。", pause=0.6),
        L("c6_6", "風が吹くと、まっすぐ持った傘では、走ったほうが濡れません。", pause=0.5),
        L("c6_7", "では、さっきのように、傘を雨に向けたら？", pause=0.4),
        L("c6_8", "追い風では、歩く人には後ろから。風より速い走る人には、前から雨が来ます。", pause=0.2),
        L("c6_8b", "歩く人は後ろへ、走る人は前へ傾けます。", pause=0.4),
        L("c6_9", "歩いても、走っても、{0粒|ゼロつぶ}。", pause=0.85),
        L("c6_10", "向かい風では、歩いても{約5,000粒|約五千粒}、走っても{約4,900粒|約四千九百粒}。ほとんど同じです。", pause=0.3),
        L("c6_10b", "傘を前に出しても、{0|ゼロ}にはなりません。", pause=0.4),
        L("c6_11", "風の日は、速さより、傘を雨に向けるほうが効きます。", pause=0.8),
        C(CH_TITLES[6], id="ch6", gap=1.2),
        L("c7_1", "答えは、傘を持っているかで、逆になります。", pause=0.4),
        L("c7_2", "傘なしなら、走る。{約3割|約三割}減ります。", pause=0.3),
        L("c7_3", "傘ありなら、歩く。まっすぐ持つと、走るほうが{約6倍|約六倍}濡れます。", pause=0.4),
        L("c7_4", "傘を雨に向けて前に出せば、歩けば{0粒|ゼロつぶ}。走っても{約2,000粒|約二千粒}まで減ります。", pause=0.4),
        L("c7_5", "風が吹くと、話が変わります。", pause=0.2),
        L("c7_5b", "まっすぐ持った傘なら、走るほうが少ない。", pause=0.3),
        L("c7_5c", "傘を雨に向ければ、追い風は{0粒|ゼロつぶ}、向かい風は歩いても走ってもほぼ同じでした。", pause=0.5),
        L("c7_6", "ただし、これは単純にしたモデルです。", pause=0.3),
        L("c7_7", "傘は平らな円板。", pause=0.2),
        L("c7_7b", "人は箱の形で、{雨粒|あまつぶ}は全部{2mm|二ミリ}。風は一定です。", pause=0.3),
        L("c7_8", "歩きの数字は、傘の大きさと持つ高さで大きく動きます。", pause=0.2),
        L("c7_8b", "まっすぐ持つと、持つ高さが{10cm|十センチ}違うだけで、粒数は倍以上変わります。", pause=0.4),
        L("c7_9", "それでも、風がなければ、「傘ありなら、ゆっくり」は、どの傘でも、どの持ち方でも変わりませんでした。", pause=0.8),
        L("c8_1", "傘があっても、走るほうが濡れない。そう思っていました。", pause=0.4),
        L("c8_2", "進むと、雨は前から来る。走るほど、傘の影からはみ出します。", pause=0.5),
        L("c8_3", "雨の日、あなたは傘をどう持っていましたか？", pause=1),
        L("c8_4", "このチャンネルでは、こんなふうにシミュレーションで確かめる動画を上げていきます。", pause=0.3),
        L("c8_5", "よければ、チャンネル登録と高評価をお願いします。", pause=0),
        G("g_end", 2.0),   # 言い終わって約2秒で終わる（合戦ロングと同じ。終了画面の要素は重ねない）
    ]


@dataclass
class _FakeClip:
    """--fake-voice 用の無音（長さは字数からの見積もり）"""
    text: str
    spoken: str
    duration: float

    def samples(self):
        return np.zeros(16, np.float32)


def _fake_synth(text_, cache_dir, speed=SPEED, **kw):
    shown, spoken = split_reading(text_)
    n = len(shown) + sum(max(0, len(m.group(2)) * 0.55 - len(m.group(1)))
                         for m in __import__("re").finditer(r"\{([^{}|]*)\|([^{}]*)\}", text_))
    return _FakeClip(shown, spoken, 0.25 + n * 0.158 / speed)


# 字幕の折り返しを指定する文（自動だと語の途中で折れるもの）。この動画の中だけで差し替える
_SUB_BREAK = {
    "傘をさして歩いた約1,100粒は、傘なしで走った約9,300粒の、1割ちょっとです。": ["傘をさして歩いた約1,100粒は、", "傘なしで走った約9,300粒の、1割ちょっとです。"],
    "傘なしは、速いほど減る。傘ありは、速いほど増える。向きが逆です。": ["傘なしは、速いほど減る。", "傘ありは、速いほど増える。向きが逆です。"],
    "傘ありでは、速いほど体が影からはみ出して、前から当たる雨が増えます。": ["傘ありでは、速いほど体が影からはみ出して、", "前から当たる雨が増えます。"],
    "歩く人は、12度。約900粒まで減りました。約2割減です。": ["歩く人は、12度。", "約900粒まで減りました。約2割減です。"],
    "傾けても、地面から約125cmまで濡れます。脚と腰は、やはり濡れます。": ["傾けても、地面から約125cmまで濡れます。", "脚と腰は、やはり濡れます。"],
    "直径1m20cmの大きな傘。歩くと、0粒。走ると、約6,000粒。": ["直径1m20cmの大きな傘。", "歩くと、0粒。走ると、約6,000粒。"],
    "風は秒速3m。雨粒も、落ちながら横に秒速3mで流れるとします。": ["風は秒速3m。雨粒も、落ちながら", "横に秒速3mで流れるとします。"],
    "向かい風では、傘をさしても、歩きで防げるのは3〜4割。走ると、もっと防げません。": ["向かい風では、傘をさしても、歩きで防げるのは3〜4割。", "走ると、もっと防げません。"],
    "それでも、風がなければ、「傘ありなら、ゆっくり」は、どの傘でも変わりませんでした。": ["それでも、風がなければ、", "「傘ありなら、ゆっくり」は、どの傘でも変わりませんでした。"],
}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)


# 一呼吸（2026-10-12 ユーザー「数字がいっぱい出てくるので、句読点で一呼吸、ページの切り替わりで一呼吸。ただしテンポは大事」）
#   文の中: 読点「、」と句点「。」の後ろで切って合成し、無音を足す（engine/voice.py の synth(pauses=...)）
#   数字を言った文の後と、章の切り替わり（付箋の前後）に少し長めの間
VOICE_PAUSES = (0.10, 0.22)          # (読点の後, 句点の後) に足す無音（秒）。塊の前後の無音 0.17秒 に上乗せ
NUM_BREATH = 0.25                    # 数字を言った文の後に足す間（秒）
CH_BREATH = 0.35                     # 章の付箋の間に足す（秒）


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and any(ch.isdigit() for ch in split_reading(it.text)[0]) and it.id != "c8_5":
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


def _timeline():
    return lf.Timeline(_breathe(_items()), VOICE_DIR, lead=3.0,
                       synth=_fake_synth if (FAKE or _WORKER) else _voice_synth)


tl = _timeline()
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ============================================================
# 小さな道具（合戦ロングと同じ）
# ============================================================
def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    """t1 から d 秒で 1→0"""
    return 1 - clamp01((t - t1) / d)


def prog(t, t0, s, cps=9.0):
    return clamp01((t - t0) / lf.write_dur(s, cps))


def wr(ctx, s, x, y, size, color, t0, t, cps=9.0, align="left", alpha=1.0, bold=True):
    """t0 から手書きで書き進む文字（書き終わったらそのまま残る）"""
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


def fit(s, size, maxw, bold=True):
    w = text_width(s, size, bold)
    return size if w <= maxw else max(26.0, size * maxw / w)


def kf(t, pts):
    """キーフレーム [(時刻, 値), ...]（時刻順）を ease でつなぐ。範囲の外は端の値"""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t < t1:
            if t1 - t0 < 1e-9:
                return v1
            return v0 + (v1 - v0) * ease((t - t0) / (t1 - t0))
    return pts[-1][1]


class Track:
    """時間で変わる値（止まる・動く、傘の開き・大きさ・傾き など）。to(t, v, d) で t から d 秒かけて v へ"""

    def __init__(self, v0):
        self.pts = [(-10.0, v0)]

    def to(self, t, v, d=0.4):
        t = max(t, self.pts[-1][0])
        self.pts += [(t, self.pts[-1][1]), (t + d, v)]
        return self

    def __call__(self, t):
        return kf(t, self.pts)


def tag(ctx, s, x, y, size, col, a=1.0, progress=1.0):
    """白い下地つきの札（絵の上に置く字）"""
    if a <= 0.003 or progress <= 0:
        return
    w = text_width(s, size) + 26
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, x - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, x, y, size, col, progress, align="center", alpha=a)


def pen_arrow(ctx, x0, y0, x1, y1, color, seed, width=6, alpha=1.0, head=22):
    """ペンで引いた矢印（ショートと同じ形）"""
    pen_line(ctx, x0, y0, x1, y1, color, seed=seed, width=width, alpha=alpha)
    ang = math.atan2(y1 - y0, x1 - x0)
    for sgn in (-1, 1):
        a2 = ang + math.pi + sgn * 0.5
        pen_line(ctx, x1, y1, x1 + head * math.cos(a2), y1 + head * math.sin(a2), color, seed=seed + 3 * sgn,
                 width=width, alpha=alpha)


def legend_at(ctx, items, cx, y, size=30, gap=48, a=1.0):
    """色の見本と説明を cx を中心に並べる（note.legend の中心を動かせる版）"""
    ws = [44 + text_width(lab, size, bold=False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.stroke()
        text(ctx, lab, x + 44, y, size, INK, align="left", bold=False, alpha=a)
        x += w + gap


# ============================================================
# 絵: 人（ショート ame-hashiru.py の draw_person をコピー。傘を持つ腕 grip を足した）
# ============================================================
WALK_COL, RUN_COL = "#a9d0f2", "#c5e37a"            # ショートと同じ: 歩く人は水色、走る人は黄緑のうすい塗り
SKY, ORANGE = "#3a8fd9", "#f29a2e"                  # 青＝上から、橙＝前から（ショートと同じ）
RAIN_COL = "#4f8fd0"
UMB_COL = {"walk": INK, "run": RED}                 # 傘: 左の歩く人は墨色、右の走る人は赤（最後まで入れ替えない）
PUR, ORG = "#6a4fb3", "#e8871e"                     # 散布図: 傘なし（ショートの無風と同じ紫）／傘あり（橙）
CROWD_COL, CROWD_UMB = "#e6dfcf", "#8a8f9e"         # 1万人の小さな人（役の色と混ざらない灰色）


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


def _ik(sh, g, l1=22.0, l2=20.0):
    """肩から手 g へ届く腕（肘は下側に曲げる）。届かなければ g の向きにいっぱいに伸ばす"""
    dx, dy = g[0] - sh[0], g[1] - sh[1]
    d = max(4.0, min(l1 + l2 - 0.5, math.hypot(dx, dy)))
    ang = math.atan2(dy, dx)
    A = math.acos(max(-1.0, min(1.0, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    cands = [(sh[0] + l1 * math.cos(ang + s_ * A), sh[1] + l1 * math.sin(ang + s_ * A)) for s_ in (1, -1)]
    el = max(cands, key=lambda p: p[1])
    return [sh, el, (sh[0] + d * math.cos(ang), sh[1] + d * math.sin(ang))]


def draw_person(ctx, x, gy, h, col, phase, run, amp=1.0, a=1.0, grip=None, eye_out=None):
    """横から見た人（右向き）。足元が (x, gy)。phase は歩調。amp=0 で立ち止まる。
    grip=(dx, dy) は傘を持つ所（足元からの画面 px）。奥の手で持つ（体と頭の後ろを通るので、腕が顔の前を横切らない）。
    手前の手は振る。None なら両手を振る。戻り値: 持つ手（grip がなければ手前の手）の位置（画面 px）。
    eye_out にリストを渡すと、(目の x, 目の y, 縮尺) を足す（当たった粒を目の上に描かないため）"""
    if a <= 0:
        return (x, gy)
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
    _limb(ctx, leg(1), 17, dark)
    a1 = _ik(sh, (grip[0] / s, grip[1] / s), 27.0, 25.0) if grip is not None else arm(1)
    _limb(ctx, a1, 12, dark)
    _limb(ctx, [hip, sh], 29, col)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.arc(hd[0], hd[1], 18.3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#fff3df"))
    ctx.arc(hd[0], hd[1], 15.5, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.arc(hd[0] + 8, hd[1] - 2, 2.4, 0, 2 * math.pi)
    ctx.fill()
    _limb(ctx, leg(0), 17, col)
    a0 = arm(0)
    _limb(ctx, a0, 12, col)
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()
    if eye_out is not None:
        eye_out.append((x + (hd[0] + 8) * s, gy + (hd[1] - 2) * s, s))
    hand = a1 if grip is not None else a0
    return (x + hand[-1][0] * s, gy + hand[-1][1] * s)


# ============================================================
# 絵: 雨の線（ショートの draw_rain をコピー。見かけの傾き slant と、傘の影を抜く clip を足した）
# ============================================================
_RR = np.random.default_rng(4)
N_RAIN = 130
R_U = _RR.uniform(0, 1, N_RAIN)
R_PH = _RR.uniform(0, 1000, N_RAIN)
R_SP = _RR.uniform(700, 1050, N_RAIN)
R_LN = _RR.uniform(32, 54, N_RAIN)
R_WD = _RR.uniform(2.2, 3.4, N_RAIN)
R_AL = _RR.uniform(0.38, 0.8, N_RAIN)
R_FRONT = _RR.random(N_RAIN) < 0.25


def draw_rain(ctx, t, x0, x1, y0, y1, slant, front, a=1.0, shift=0.0, dens=1.0, fade_px=50.0):
    """雨の線。slant は1px落ちるあいだに横へ進む px（体から見た雨の傾き c/U。負なら前＝右から来る）。
    front=True なら手前の層だけ、False なら奥の層だけ"""
    if a <= 0:
        return
    span, wdt = y1 - y0, x1 - x0
    norm = 1.0 / math.sqrt(1 + slant * slant)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    r = hexrgb(RAIN_COL)
    sel = np.where(R_FRONT == front)[0]
    sel = sel[:max(1, int(len(sel) * dens))]
    for i in sel:
        L = R_LN[i]
        yy = y0 + ((R_PH[i] + shift + R_SP[i] * t) % (span + L)) - L
        xx = x0 + ((R_U[i] * wdt + shift * 0.37 + slant * (yy - y0)) % wdt)
        ly = L * norm
        ym = yy + ly / 2
        fd = clamp01(min((ym - y0) / fade_px, (y1 - ym) / 8.0)) if fade_px > 0 else 1.0
        ctx.set_source_rgba(r[0], r[1], r[2], R_AL[i] * a * fd * (0.55 if front else 1.0))
        ctx.set_line_width(R_WD[i])
        ctx.move_to(xx, yy)
        ctx.line_to(xx + slant * ly, yy + ly)
        ctx.stroke()


def clip_out(ctx, poly):
    """poly の内側を描かない clip（いまの clip と重ねる）"""
    ctx.rectangle(-50, -50, lf.W + 100, lf.H + 100)
    ctx.move_to(*poly[0])
    for p in poly[1:]:
        ctx.line_to(*p)
    ctx.close_path()
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.clip()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)


# ============================================================
# 絵: 傘（新しく描く。モデルどおり「体の真上・高さ HU の円板」の断面。下の縁は円板＝まっすぐ、上だけ少しふくらませる）
# ============================================================
K = 180.0                                           # 1m あたりの px（体の高さ1.7m ＝ 306px）
FIG_H = BH * K
GY = 780.0                                          # 地面の高さ
COLS = {"walk": dict(cx=300.0, x0=116.0, x1=503.0, shift=0.0, step=1.6, run=False, col=WALK_COL),
        "run": dict(cx=712.0, x0=507.0, x1=898.0, shift=517.0, step=3.0, run=True, col=RUN_COL)}
RAIN_TOP = 296.0


def umb_ends(cx, gy, du, phi, k=K, hu=HU, ux=0.0):
    """円板の前の縁 F と後ろの縁 B（画面 px）。前へ傾ける（phi>0）と前の縁が下がる。
    ux・hu は円板の中心（体の中心から前へ ux m、高さ hu m。4章（改）の腕を伸ばすモデルの center）"""
    R = du / 2 * k
    ph = math.radians(phi)
    Cx, Cy = cx + ux * k, gy - hu * k
    return (Cx + R * math.cos(ph), Cy + R * math.sin(ph)), (Cx - R * math.cos(ph), Cy - R * math.sin(ph))


def shadow_poly(cx, gy, du, phi, slant, k=K, ux=0.0, hu=HU):
    """傘の影（雨の来る向きに沿って、円板の縁から地面まで）。体の中心線の断面"""
    F, B = umb_ends(cx, gy, du, phi, k, hu=hu, ux=ux)
    return [B, F, (F[0] + slant * (gy - F[1]), gy), (B[0] + slant * (gy - B[1]), gy)]


def draw_umbrella(ctx, cx, gy, du, phi, col, u=1.0, a=1.0, k=K, lw=3.0, part="all", dome=0.17, ux=0.0, hu=HU):
    """開いた傘。u は開き具合（0〜1）。柄は円板の中心から体のほうへ（円板に垂直）。
    part="handle" は柄だけ（人の後ろに描く）、"canopy" は布だけ（人の前に描く）"""
    if a <= 0.003 or u <= 0.01:
        return
    uu = ease(u)
    R = du / 2 * k * (0.2 + 0.8 * uu)
    ph = math.radians(phi)
    ex, ey = math.cos(ph), math.sin(ph)
    nx, ny = math.sin(ph), -math.cos(ph)               # 上向きの法線（画面）
    Cx, Cy = cx + ux * k, gy - hu * k
    Fx, Fy = Cx + R * ex, Cy + R * ey
    Bx, By = Cx - R * ex, Cy - R * ey
    bul = dome * du / 2 * k * uu
    ctx.save()
    if a < 1:
        ctx.push_group()
    # 柄（円板の中心から体のほうへ。握る手まで handle_len。その先に少し曲がり）
    L = (handle_len(phi) + 0.04) * k
    if part in ("all", "handle"):
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.set_line_width(max(2.0, 5.0 * k / K))
        gx, gy2 = Cx - L * nx, Cy - L * ny
        ctx.move_to(Cx, Cy)
        ctx.line_to(gx, gy2)
        ctx.stroke()
        ctx.arc_negative(gx + 0.045 * k * ex, gy2 + 0.045 * k * ey, 0.045 * k, math.atan2(-ey, -ex), math.atan2(-ey, -ex) - math.pi)
        ctx.stroke()
    if part == "handle":
        if a < 1:
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
        ctx.restore()
        return
    # 布: 上は丸く、下の縁（円板）はほぼまっすぐ。骨のあいだを少しだけへこませる
    ctx.move_to(Bx, By)
    for i in range(1, 25):
        s_ = i / 24
        b = bul * 4 * s_ * (1 - s_)
        ctx.line_to(Bx + (Fx - Bx) * s_ + nx * b, By + (Fy - By) * s_ + ny * b)
    nrib = 6
    for i in range(nrib, 0, -1):
        s0, s1 = i / nrib, (i - 1) / nrib
        sm = (s0 + s1) / 2
        p1 = (Bx + (Fx - Bx) * s1, By + (Fy - By) * s1)
        cm = (Bx + (Fx - Bx) * sm + nx * 0.05 * R, By + (Fy - By) * sm + ny * 0.05 * R)
        ctx.curve_to(cm[0], cm[1], cm[0], cm[1], p1[0], p1[1])
    ctx.close_path()
    c = hexrgb(col)
    ctx.set_source_rgba(c[0], c[1], c[2], 0.95)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(lw * k / K)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.stroke()
    # 骨（うすく）と石突き
    top = (Cx + nx * bul, Cy + ny * bul)
    ctx.set_source_rgba(1, 1, 1, 0.28)
    ctx.set_line_width(max(1.5, 2.0 * k / K))
    for i in range(1, nrib):
        s_ = i / nrib
        ctx.move_to(*top)
        ctx.line_to(Bx + (Fx - Bx) * s_, By + (Fy - By) * s_)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(max(2.0, 4.0 * k / K))
    ctx.move_to(*top)
    ctx.line_to(top[0] + nx * 0.07 * k, top[1] + ny * 0.07 * k)
    ctx.stroke()
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


HAND_DROP = 0.15   # 絵の人の肩（約1.23m。頭を大きく描いているぶん低い）とモデルの肩 1.45m の差に合わせ、握る所を柄の線に沿って下げる（m）


def handle_len(phi):
    """絵の柄の長さ（円板の中心から握る手まで）。モデルの柄 LS に、手を HAND_DROP 下げたぶんを足す"""
    return LS + HAND_DROP / max(0.3, math.cos(math.radians(phi)))


def grip_point(cx, gy, phi, k=K, ux=0.0, hu=HU):
    """柄を握る手の位置（足元からの画面 px）。円板の中心から、柄の線（円板に垂直）に沿って handle_len(phi) の所。
    傘の円板の位置と傾きはモデル（arm_search の center・phi）のまま。手だけ、絵の人の肩の低さに合わせて柄の線上を下げる"""
    ph = math.radians(phi)
    L = handle_len(phi)
    return ((ux - L * math.sin(ph)) * k, -(hu - L * math.cos(ph)) * k)


def draw_closed_umbrella(ctx, hx, hy, gy, col, a=1.0):
    """閉じた傘（手に提げる）。手から地面の少し上まで、少し前に傾ける"""
    if a <= 0.003:
        return
    tip = (hx + 0.16 * K, gy - 0.05 * K)
    top = (hx + 0.012 * K, hy + 0.10 * K)
    dx, dy = tip[0] - top[0], tip[1] - top[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    ctx.save()
    ctx.push_group()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(5)
    ctx.move_to(hx, hy)
    ctx.line_to(*top)
    ctx.stroke()
    ctx.arc(hx - 0.04 * K, hy, 0.04 * K, 0, math.pi)       # 柄の曲がり
    ctx.stroke()
    w0, w1 = 13.0, 4.0
    ctx.move_to(top[0] + px * w0, top[1] + py * w0)
    ctx.line_to(top[0] + ux * L * 0.35 + px * (w0 + 3), top[1] + uy * L * 0.35 + py * (w0 + 3))
    ctx.line_to(tip[0] + px * w1, tip[1] + py * w1)
    ctx.line_to(tip[0] - px * w1, tip[1] - py * w1)
    ctx.line_to(top[0] + ux * L * 0.35 - px * (w0 + 3), top[1] + uy * L * 0.35 - py * (w0 + 3))
    ctx.line_to(top[0] - px * w0, top[1] - py * w0)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(col, 0.95))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.move_to(*tip)
    ctx.line_to(tip[0] + ux * 12, tip[1] + uy * 12)
    ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ============================================================
# 絵: 体に当たった雨粒（ショートの HitLayer をコピー。大きさを左ページに合わせ、時刻と高さは雨粒をまいた見本から）
# ============================================================
LAY_X0, LAY_W = -80, 160
LAY_Y0 = -int(FIG_H) - 30
LAY_H = int(FIG_H) + 44
_OFF = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (1, 2)]


def record(v, w, seed, Du, phi, hu=HU, cx=0.0):
    """1人ぶん、雨粒をまいて当たった粒を記録する（モデルの _drops / _test をそのまま使う。person_mc と同じ乱数の使い方）。
    hu・cx は円板の中心の高さと前への位置（4章（改）の腕を伸ばすモデル）"""
    rng = np.random.default_rng(seed)
    T = D / v
    x0, y0, z0, c = _drops(w - v, T, rng)
    hit, ti, top = _test(x0, y0, z0, c, T, Du, hu, phi, cx=cx)
    t_in = ti[hit]
    zz = z0[hit] - U * t_in
    o = np.argsort(t_in)
    return dict(t=t_in[o], top=top[hit][o], z=zz[o], n=int(hit.sum()), T=T)


class HitLayer:
    """1人ぶんの当たった粒を、体の座標（足元が原点）の画像に点で積む。青＝上から、橙＝前から"""

    def __init__(self, r, seed, back=False):
        n = r["n"]
        g = np.random.default_rng(seed)
        top = r["top"]
        self.t, self.top = r["t"], top
        xt = g.uniform(-22, 22, n)                                # 上から: 頭のてっぺん（目より上）
        yt = -FIG_H - 4 + g.random(n) * 20
        xf = 4 + g.random(n) * 28                                 # 前から: 体の前側（雨が後ろから来るなら後ろ側）
        if back:
            xf = -xf
        yf = -r["z"] * K
        self.px = np.where(top, xt, xf)
        self.py = np.where(top, yt, yf)
        self._last = (None, None)

    def count(self, tau):
        return int(np.searchsorted(self.t, tau, side="right"))

    def image(self, k, alpha=0.30):
        if self._last[0] == k:
            return self._last[1][0]
        ix = np.round(self.px[:k] - LAY_X0).astype(np.int64)
        iy = np.round(self.py[:k] - LAY_Y0).astype(np.int64)
        tp = self.top[:k]
        cov_t = np.zeros(LAY_W * LAY_H)
        cov_f = np.zeros(LAY_W * LAY_H)
        for dx, dy in _OFF:
            x2, y2 = ix + dx, iy + dy
            ok = (x2 >= 0) & (x2 < LAY_W) & (y2 >= 0) & (y2 < LAY_H)
            idx = y2 * LAY_W + x2
            cov_t += np.bincount(idx[ok & tp], minlength=LAY_W * LAY_H)
            cov_f += np.bincount(idx[ok & ~tp], minlength=LAY_W * LAY_H)
        at = 1 - (1 - alpha) ** cov_t
        af = 1 - (1 - alpha) ** cov_f
        ct, cf = hexrgb(SKY), hexrgb(ORANGE)
        out = np.zeros((LAY_H, LAY_W, 4), np.uint8)
        al = at + af * (1 - at)
        for c, kk in ((2, 0), (1, 1), (0, 2)):
            pm = ct[c] * at + cf[c] * af * (1 - at)
            out[:, :, kk] = (pm.reshape(LAY_H, LAY_W) * 255).astype(np.uint8)
        out[:, :, 3] = (al.reshape(LAY_H, LAY_W) * 255).astype(np.uint8)
        out = np.ascontiguousarray(out)
        surf = cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, LAY_W, LAY_H, LAY_W * 4)
        self._last = (k, (surf, out))
        return surf


# 見本（1人ぶん）の条件。種は「期待値にいちばん近い結果」になるものを探して選ぶ（画面の数字は (a) 期待値から出す）
# 4章（改）・6章の「腕の届く範囲で傘を前に出して傾ける」置き方（data.json の ch4b。モデルの arm_search の結果）
CB = RES["ch4b"]


def _arm(rows, v, key):
    r = next(r for r in rows if abs(r["v"] - v) < 1e-9)[key]
    return dict(phi=float(r["phi"]), cx=float(r["center"][0]), hu=float(r["center"][1]), hand=r["hand"], e=float(r["e"]),
                z_dry_center=float(r["z_dry_center"]), z_dry_edge=float(r["z_dry_edge"]))


ARM_CALM = {"walk": _arm(CB["calm"], V_WALK, "ii"), "run": _arm(CB["calm"], V_RUN, "ii")}
ARM_TAIL = {"walk": _arm(CB["wind_behind"]["tail"], V_WALK, "iib"), "run": _arm(CB["wind_behind"]["tail"], V_RUN, "iib")}
ARM_HEAD = {"walk": _arm(CB["wind_behind"]["head"], V_WALK, "iib"), "run": _arm(CB["wind_behind"]["head"], V_RUN, "iib")}


def _sd(v, w, du, a=None):
    return (v, w, du, a["phi"], a["hu"], a["cx"]) if a else (v, w, du, 0.0, HU, 0.0)


SAMPLE_DEFS = {   # 名前: (速さ, 風, 直径, 傾き, 円板の高さ, 円板の前への位置)
    "walk_plain": _sd(V_WALK, 0.0, 0.0), "run_plain": _sd(V_RUN, 0.0, 0.0),
    "walk_flat": _sd(V_WALK, 0.0, DU), "run_flat": _sd(V_RUN, 0.0, DU),
    "walk_arm": _sd(V_WALK, 0.0, DU, ARM_CALM["walk"]), "run_arm": _sd(V_RUN, 0.0, DU, ARM_CALM["run"]),
    "walk_fold": _sd(V_WALK, 0.0, UMBRELLAS["折りたたみ傘"][0]), "run_fold": _sd(V_RUN, 0.0, UMBRELLAS["折りたたみ傘"][0]),
    "walk_big": _sd(V_WALK, 0.0, UMBRELLAS["ゴルフ傘"][0]), "run_big": _sd(V_RUN, 0.0, UMBRELLAS["ゴルフ傘"][0]),
    "walk_tail14": _sd(V_WALK, WIND, DU), "run_tail": _sd(V_RUN, WIND, DU),
    "walk_head": _sd(V_WALK, -WIND, DU), "run_head": _sd(V_RUN, -WIND, DU),
    "walk_tail_arm": _sd(V_WALK, WIND, DU, ARM_TAIL["walk"]), "run_tail_arm": _sd(V_RUN, WIND, DU, ARM_TAIL["run"]),
    "walk_head_arm": _sd(V_WALK, -WIND, DU, ARM_HEAD["walk"]), "run_head_arm": _sd(V_RUN, -WIND, DU, ARM_HEAD["run"]),
}


def _pick_seeds():
    f = OUT / "scene_seeds.json"
    have = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    changed = False
    for name, (v, w, du, phi, hu, cx) in SAMPLE_DEFS.items():
        key = f"{v}|{w}|{du}|{phi:.4f}|{hu:.4f}|{cx:.4f}"
        if have.get(name, {}).get("key") == key:
            continue
        e = expected(v, w, du, hu, phi, cx=cx)
        best = None
        for s_ in range(1, 81):
            n = person_mc(v, w, 7000 + s_, du, hu, phi, cx=cx)
            z = abs(n - e)
            if best is None or z < best[0]:
                best = (z, 7000 + s_, n)
            if z <= 0.5 + 0.03 * math.sqrt(max(e, 1.0)):
                break
        have[name] = dict(key=key, seed=best[1], n=best[2], e=e)
        changed = True
    if changed and not _WORKER:
        f.write_text(json.dumps(have, ensure_ascii=False, indent=1), encoding="utf-8")
    return have


SEEDS = _pick_seeds()
_LAYERS = {}


def layer(name):
    if name not in _LAYERS:
        v, w, du, phi, hu, cx = SAMPLE_DEFS[name]
        _LAYERS[name] = HitLayer(record(v, w, SEEDS[name]["seed"], du, phi, hu, cx), 11 + len(_LAYERS), back=(w - v) > 0)
    return _LAYERS[name]


# ============================================================
# 時間割の上の「状態」（止まる・動く、傘、風、点の見本）。この役・色・位置は最後まで入れ替えない
# ============================================================
TW_RUN, TW_WALK = D / V_RUN, D / V_WALK             # 100m にかかる秒（世界の時間）: 20秒・71.4秒


class Run:
    """100m を進む場面の時計（早回し）。走る人がゴールするまで p1 秒、そこから歩く人がゴールするまで p2 秒（動画の秒）"""

    def __init__(self, t0, p1, p2):
        self.t0, self.p1, self.p2 = t0, p1, p2

    def tau(self, t):
        u = t - self.t0
        if u <= 0:
            return 0.0
        if u < self.p1:
            return TW_RUN * u / self.p1
        return min(TW_WALK, TW_RUN + (TW_WALK - TW_RUN) * (u - self.p1) / self.p2)

    def video_of(self, tau):
        if tau <= TW_RUN:
            return self.t0 + self.p1 * tau / TW_RUN
        return self.t0 + self.p1 + self.p2 * (tau - TW_RUN) / (TW_WALK - TW_RUN)

    def finish(self, col):
        return self.t0 + self.p1 + (self.p2 if col == "walk" else 0.0)

    def progress(self, t, col):
        v = V_WALK if col == "walk" else V_RUN
        return clamp01(v * self.tau(t) / D)


RUN0 = Run(S("c0_6") + 0.6, 2.4, 4.2)               # 傘なし（ショートのおさらい・早回し）
RUN1 = Run(S("c2_1") + 0.8, 3.7, 4.1)               # 傘あり（2章の 2a）
RUNS = (RUN0, RUN1)


class Fill:
    """風の場面などで、点が t0〜t1 の間にたまる（世界の時間 T 秒ぶんを一様に早回し）"""

    def __init__(self, t0, t1, T):
        self.t0, self.t1, self.T = t0, t1, T

    def tau(self, t):
        return self.T * clamp01((t - self.t0) / (self.t1 - self.t0))


# 動く（1）・止まる（0）
AMP = {c: Track(0.0) for c in COLS}
for c in COLS:
    AMP[c].to(RUN0.t0 - 0.15, 1.0, 0.3).to(RUN0.finish(c), 0.0, 0.35)
    AMP[c].to(RUN1.t0 - 0.15, 1.0, 0.3).to(RUN1.finish(c), 0.0, 0.35)
    AMP[c].to(S("c3_3") + 0.15, 1.0, 0.6)
# 進む速さ（世界の m/s。雨の見かけの傾きに使う）
VEL = {"walk": Track(V_WALK), "run": Track(V_RUN)}
WIND_T = Track(0.0).to(S("c6_2") + 0.6, WIND, 1.0).to(S("c6_5") + 0.0, -WIND, 1.0).to(S("c6_7") + 0.3, WIND, 1.0) \
    .to(S("c6_10") + 0.0, -WIND, 1.0).to(S("ch6"), 0.0, 0.8)
OPEN = Track(1.0).to(S("c0_6") + 0.1, 0.0, 0.6).to(S("c0_8") + 0.25, 1.0, 0.7)
DU_T = Track(DU).to(S("c5_2") + 0.2, UMBRELLAS["折りたたみ傘"][0], 0.6).to(S("c5_3") + 0.2, UMBRELLAS["ゴルフ傘"][0], 0.7) \
    .to(S("ch5") + 0.2, DU, 0.6)
# 傘の傾き（度）・円板の中心（前へ m・高さ m）・人の位置のずらし（px。向かい風で傘を大きく前に出すとき、列からはみ出さないように）
PHI = {c: Track(0.0) for c in COLS}
UX = {c: Track(0.0) for c in COLS}
HZ = {c: Track(HU) for c in COLS}
XOFF = {c: Track(0.0) for c in COLS}


def hold(col, t, a=None, d=0.8, xoff=None):
    """t から d 秒かけて、傘を置き方 a（None なら まっすぐ・体の真上）へ"""
    ph, ux, hu = (a["phi"], a["cx"], a["hu"]) if a else (0.0, 0.0, HU)
    PHI[col].to(t, ph, d)
    UX[col].to(t, ux, d)
    HZ[col].to(t, hu, d)
    if xoff is not None:
        XOFF[col].to(t, xoff, d)


# 4章: 腕の届く範囲でいろいろ試す → 雨の傾きに → 歩く人は少し前へ・走る人は70cm前へ
_try = (dict(phi=40.0, cx=0.35, hu=1.95), dict(phi=15.0, cx=0.10, hu=1.90), dict(phi=30.0, cx=0.45, hu=1.80))
for c, off in (("walk", 0.0), ("run", 0.12)):
    for i, a_ in enumerate(_try):
        hold(c, mid("c4_2b", 0.08 + off + 0.27 * i), a_, 0.22 * dur("c4_2b"))
    th = apparent_angle(V_WALK if c == "walk" else V_RUN)
    hold(c, S("c4_3") + 0.1, dict(phi=th, cx=0.15, hu=HU), 0.8)
hold("walk", S("c4_4") + 0.1, ARM_CALM["walk"], 0.8)
hold("run", S("c4_5") + 0.2, ARM_CALM["run"], 1.2)
for c in COLS:
    hold(c, S("ch4") + 0.1, None, 0.6)
# 6章: まっすぐ → 雨に向ける（追い風: 歩く人は後ろへ・走る人は前へ）→ 向かい風で前へ大きく
hold("walk", S("c6_8b") + 0.1, ARM_TAIL["walk"], 0.9)
hold("run", mid("c6_8b", 0.5), ARM_TAIL["run"], 0.9)
hold("walk", S("c6_10") + 0.2, ARM_HEAD["walk"], 1.0, xoff=-70.0)
hold("run", S("c6_10") + 0.2, ARM_HEAD["run"], 1.0, xoff=-95.0)
for c in COLS:
    hold(c, S("ch6") + 0.1, None, 0.6, xoff=0.0)
# 7章: 「傘を雨に向けて前に出せば」の間だけ、4章の置き方に
for c in COLS:
    hold(c, S("c7_4") + 0.2, ARM_CALM[c], 0.8)
    hold(c, S("c7_5") + 0.1, None, 0.6)
SHADOW_A = Track(0.07).to(S("c3_2"), 0.22, 0.6).to(S("ch3"), 0.15, 0.6).to(S("ch6"), 0.10, 0.6)


def umb_state(col, t):
    """(傾き, 中心の前への位置 m, 中心の高さ m)"""
    return PHI[col](t), UX[col](t), HZ[col](t)


def velrel(col, t):
    """体から見た雨の横の速さ c = w − v（負なら雨は前から）"""
    return WIND_T(t) - VEL[col](t) * AMP[col](t)


# 点の見本（どの見本を、いつ出して、いつ消すか）。fill が None なら最初から全部
_EP = []


def ep(col, name, t_on, t_off, fill_=None, d_in=0.5, d_out=0.5):
    _EP.append(dict(col=col, name=name, on=t_on, off=t_off, fill=fill_, d_in=d_in, d_out=d_out))


T_END = 1e9
ep("walk", "walk_plain", RUN0.t0, S("c0_8") + 0.05, RUN0.tau, 0.01)
ep("run", "run_plain", RUN0.t0, S("c0_8") + 0.05, RUN0.tau, 0.01)
ep("walk", "walk_flat", RUN1.t0, S("c4_4") + 0.5, RUN1.tau, 0.01)
ep("run", "run_flat", RUN1.t0, mid("c4_6", 0.45), RUN1.tau, 0.01)
ep("walk", "walk_arm", S("c4_4") + 0.4, S("ch4") + 0.1)
ep("run", "run_arm", mid("c4_6", 0.4), S("ch4") + 0.1)
for c in COLS:
    ep(c, f"{c}_flat", S("ch4") + 0.1, S("c5_2") + 0.4)
    ep(c, f"{c}_fold", S("c5_2") + 0.3, S("c5_3") + 0.4)
    ep(c, f"{c}_big", S("c5_3") + 0.3, S("ch5") + 0.3)
    ep(c, f"{c}_flat", S("ch5") + 0.2, S("c6_4") + 0.1)
_f4 = Fill(S("c6_4") + 0.1, mid("c6_4", 0.9), 1.0)
_f5 = Fill(S("c6_5") + 0.4, mid("c6_5n", 0.9), 1.0)
_f10 = Fill(S("c6_10") + 0.4, mid("c6_10", 0.7), 1.0)
for c, tw in (("walk", TW_WALK), ("run", TW_RUN)):
    ep(c, "walk_tail14" if c == "walk" else "run_tail", S("c6_4"), S("c6_5") + 0.1, lambda t, tw=tw: _f4.tau(t) * tw, 0.01)
    ep(c, f"{c}_head", S("c6_5") + 0.1, S("c6_7") + 0.3, lambda t, tw=tw: _f5.tau(t) * tw, 0.01)
    ep(c, f"{c}_tail_arm", S("c6_8b") + 0.6, S("c6_10") + 0.1)
    ep(c, f"{c}_head_arm", S("c6_10") + 0.3, S("ch6") + 0.2, lambda t, tw=tw: _f10.tau(t) * tw, 0.01)
    ep(c, f"{c}_flat", S("ch6") + 0.1, S("c7_4") + 0.5)
    ep(c, f"{c}_arm", S("c7_4") + 0.5, S("c7_5") + 0.3)
    ep(c, f"{c}_flat", S("c7_5") + 0.3, T_END)


def episodes(col, t):
    for e in _EP:
        if e["col"] != col or t < e["on"] or t > e["off"] + e["d_out"]:
            continue
        a = clamp01((t - e["on"]) / e["d_in"]) * out_fade(t, e["off"], e["d_out"])
        if a <= 0.003:
            continue
        lay = layer(e["name"])
        k = len(lay.t) if e["fill"] is None else lay.count(e["fill"](t))
        yield lay, k, a


# 歩調（動画の時間）と、地面の目印の流れ（動いた分だけ足していく）
_GRID_T = np.arange(0.0, DUR + 1.0, 1 / 30)
SCROLL = {}
for c in COLS:
    sp = np.array([AMP[c](x) * VEL[c](x) * 42.0 for x in _GRID_T])
    SCROLL[c] = np.concatenate([[0.0], np.cumsum(sp[:-1]) / 30])


def scroll(col, t):
    return float(SCROLL[col][min(len(_GRID_T) - 1, max(0, int(t * 30)))])


# ============================================================
# 左ページ: 雨の道（左の列＝歩く人・墨色の傘、右の列＝走る人・赤い傘。人はその場で進み、地面が流れる）
# ============================================================
STICKY_Y = 322.0
TAG_Y = GY + 52.0
METER_Y = GY + 112.0
LABEL = {"walk": ("歩く 時速5km", "blue"), "run": ("走る 時速18km", "pink")}


def sticky_text(col, t):
    return LABEL[col][0]


def sticky_y(t):
    """名札の高さ。風の章は傘を高く・大きく前に出すので、名札と風の印を上へ逃がす"""
    return STICKY_Y - 72.0 * fade(t, S("ch5"), 0.3) * out_fade(t, S("ch6"), 0.3)


def sticky_alpha(col, t):
    a = fade(t, S("c0_4" if col == "walk" else "c0_5") + 0.3, 0.35)
    a *= 1 - fade(t, S("c2_6") - 0.3, 0.35) * out_fade(t, S("ch2") + 0.2, 0.01)     # 1万人の間は隠す
    return a


def draw_ground(ctx, col, t, a=1.0):
    c = COLS[col]
    x0, x1 = c["x0"], c["x1"]
    pen_line(ctx, x0 + 4, GY + 3, x1 - 4, GY + 2, INK, seed=11 if col == "walk" else 12, width=4, alpha=0.55 * a)
    off = scroll(col, t)
    span = x1 - x0
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for m in range(8):
        x = x0 + ((m * span / 8 + 23 * m % 17 - off) % span)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45 * a))
        ctx.set_line_width(3)
        ctx.move_to(x, GY + 16 + (m % 3) * 5)
        ctx.line_to(x + 18, GY + 16 + (m % 3) * 5)
        ctx.stroke()


def draw_column(ctx, t, col):
    c = COLS[col]
    cx, x0, x1 = c["cx"] + XOFF[col](t), c["x0"], c["x1"]
    amp = AMP[col](t)
    slant = velrel(col, t) / U
    op = OPEN(t)
    du = DU_T(t)
    phi, ux, hu = umb_state(col, t)
    shadow = shadow_poly(cx, GY, du, phi, slant, ux=ux, hu=hu) if op > 0.6 else None
    sa = SHADOW_A(t) * clamp01((op - 0.6) / 0.4)

    def rain_layer(front):
        ctx.save()
        ctx.rectangle(x0, RAIN_TOP - 10, x1 - x0, GY - RAIN_TOP + 12)
        ctx.clip()
        if shadow:
            clip_out(ctx, shadow)
        draw_rain(ctx, t, x0, x1, RAIN_TOP, GY, slant, front, shift=c["shift"])
        ctx.restore()

    def shade(alpha):
        if not shadow or alpha <= 0.003:
            return
        ctx.save()
        ctx.rectangle(x0, RAIN_TOP - 10, x1 - x0, GY - RAIN_TOP + 14)
        ctx.clip()
        ctx.move_to(*shadow[0])
        for p in shadow[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(PENCIL, alpha))
        ctx.fill()
        ctx.restore()

    rain_layer(False)
    shade(sa)
    if shadow and sa > 0:                                          # 地面に落ちた影
        xa, xb = sorted((shadow[2][0], shadow[3][0]))
        ctx.save()
        ctx.rectangle(x0, GY - 20, x1 - x0, 40)
        ctx.clip()
        ctx.translate((xa + xb) / 2, GY + 2)
        ctx.scale(max(4.0, (xb - xa) / 2), 7)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(PENCIL, min(0.5, sa * 2.2)))
        ctx.fill()
    draw_ground(ctx, col, t)
    # 人と、体に残った雨粒（体の形の上にだけ点が残る: ATOP）
    phase = 2 * math.pi * c["step"] * t
    grip = grip_point(cx, GY, phi, ux=ux, hu=hu) if op > 0.35 else None
    if op > 0:
        draw_umbrella(ctx, cx, GY, du, phi, UMB_COL[col], op, clamp01(op * 2.5), part="handle", ux=ux, hu=hu)
    ctx.push_group()
    eyes = []
    hand = draw_person(ctx, cx, GY, FIG_H, c["col"], phase, c["run"], amp, 1.0, grip, eye_out=eyes)
    for lay, k, al in episodes(col, t):
        if k <= 0:
            continue
        surf = lay.image(k)
        ctx.save()
        ctx.set_operator(cairo.OPERATOR_ATOP)
        ctx.translate(cx, GY)
        ctx.set_source_surface(surf, LAY_X0, LAY_Y0)
        ctx.paint_with_alpha(al)
        ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint()
    for ex, ey, es in eyes:                                        # 目のまわりには粒を描かない
        ctx.set_source_rgba(*hexrgb("#fff3df"))
        ctx.arc(ex - 1.0 * es, ey, 7.0 * es, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.arc(ex, ey, 2.4 * es, 0, 2 * math.pi)
        ctx.fill()
    shade(sa * 0.8)                                                # 影は体の上にも落ちる
    if op < 1:
        draw_closed_umbrella(ctx, hand[0], hand[1], GY, UMB_COL[col], 1 - clamp01(op * 2.2))
    if op > 0:
        draw_umbrella(ctx, cx, GY, du, phi, UMB_COL[col], op, clamp01(op * 2.5), part="canopy", ux=ux, hu=hu)
    rain_layer(True)


def draw_meter(ctx, t, col):
    """100m のうちどこまで進んだか（早回しの場面だけ）"""
    c = COLS[col]
    for run in RUNS:
        a = fade(t, run.t0 - 0.5, 0.3) * out_fade(t, run.finish("walk") + 1.4, 0.4)
        if a <= 0.003:
            continue
        xa, xb = c["x0"] + 72, c["x1"] - 92
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xa, METER_Y)
        ctx.line_to(xb, METER_Y)
        ctx.stroke()
        for xx in (xa, xb):
            ctx.move_to(xx, METER_Y - 9)
            ctx.line_to(xx, METER_Y + 9)
            ctx.stroke()
        text(ctx, "0m", xa - 34, METER_Y, 26, PENCIL, bold=False, alpha=a)
        text(ctx, "100m", xb + 48, METER_Y, 26, PENCIL, bold=False, alpha=a)
        p = run.progress(t, col)
        ctx.set_source_rgba(*hexrgb(UMB_COL[col], a))
        ctx.arc(xa + (xb - xa) * p, METER_Y, 9, 0, 2 * math.pi)
        ctx.fill()


# 人の足元の札（画面に出す数字は (a) 期待値の丸め）
_TAGS = {"walk": [], "run": []}


def tg(col, s_, t_on, t_off, color=None):
    _TAGS[col].append((t_on, t_off, s_, color or (INK if col == "walk" else RED)))


def _tags_init():
    c1, c4 = RES["ch1"], RES["ch4"]["umbrellas"]
    tr5 = {r["v"]: r for r in RES["ch5"]["tail"]["rows"]}
    hr5 = {r["v"]: r for r in RES["ch5"]["head"]["rows"]}
    tg("walk", f"約{fmt(r100(c1['walk_plain']))}粒", mid("c0_7", 0.4), S("c0_8") + 0.1)
    tg("run", f"約{fmt(r100(c1['run_plain']))}粒", mid("c0_7", 0.72), S("c0_8") + 0.1)
    tg("walk", f"約{fmt(r100(c1['walk_umb']))}粒", S("c2_2") + 0.2, S("ch2"))
    tg("run", f"約{fmt(r100(c1['run_umb']))}粒", S("c2_3") + 0.2, S("ch2"))
    # 4章（改）: 腕を伸ばして傾ける
    tg("walk", f"{fmt(r100(ARM_CALM['walk']['e']))}粒", mid("c4_4", 0.75), S("ch4"))
    tg("run", f"約{fmt(r100(c1['run_umb']))}粒", S("c4_6"), mid("c4_6", 0.42))
    tg("run", f"約{fmt(r100(ARM_CALM['run']['e']))}粒", mid("c4_6", 0.45), S("ch4"))
    tg("walk", f"約{fmt(r100(c4['折りたたみ傘']['walk']['flat']))}粒", mid("c5_2", 0.4), S("c5_3") + 0.3)
    tg("run", f"約{fmt(r100(c4['折りたたみ傘']['run']['flat']))}粒", mid("c5_2", 0.58), S("c5_3") + 0.3)
    tg("walk", f"{fmt(r100(c4['ゴルフ傘']['walk']['flat']))}粒", mid("c5_3", 0.45), S("ch5"))
    tg("run", f"約{fmt(r100(c4['ゴルフ傘']['run']['flat']))}粒", mid("c5_3", 0.8), S("ch5"))
    # 6章: まっすぐ（追い風・向かい風）→ 雨に向ける（追い風・向かい風）
    tg("walk", f"約{fmt(r100(tr5[V_WALK]['flat']))}粒", mid("c6_4", 0.35), S("c6_5"))
    tg("run", f"約{fmt(r100(tr5[V_RUN]['flat']))}粒", mid("c6_4", 0.7), S("c6_5"))
    tg("walk", f"約{fmt(r100(hr5[V_WALK]['flat']))}粒", mid("c6_5n", 0.3), S("c6_7") + 0.3)
    tg("run", f"約{fmt(r100(hr5[V_RUN]['flat']))}粒", mid("c6_5n", 0.65), S("c6_7") + 0.3)
    tg("walk", f"{fmt(r100(ARM_TAIL['walk']['e']))}粒", mid("c6_9", 0.3), S("c6_10"))
    tg("run", f"{fmt(r100(ARM_TAIL['run']['e']))}粒", mid("c6_9", 0.6), S("c6_10"))
    tg("walk", f"約{fmt(r100(ARM_HEAD['walk']['e']))}粒", mid("c6_10", 0.25), S("ch6"))
    tg("run", f"約{fmt(r100(ARM_HEAD['run']['e']))}粒", mid("c6_10", 0.45), S("ch6"))
    # 7章
    tg("walk", f"約{fmt(r100(c1['walk_umb']))}粒", S("ch6") + 0.6, S("c7_4") + 0.4)
    tg("run", f"約{fmt(r100(c1['run_umb']))}粒", S("ch6") + 0.6, S("c7_4") + 0.4)
    tg("walk", f"{fmt(r100(ARM_CALM['walk']['e']))}粒", S("c7_4") + 0.7, S("c7_5") + 0.2)
    tg("run", f"約{fmt(r100(ARM_CALM['run']['e']))}粒", S("c7_4") + 0.7, S("c7_5") + 0.2)
    tg("walk", f"約{fmt(r100(c1['walk_umb']))}粒", S("c7_5") + 0.5, T_END)
    tg("run", f"約{fmt(r100(c1['run_umb']))}粒", S("c7_5") + 0.5, T_END)


_tags_init()


def draw_tags(ctx, t, col):
    for (t0, t1, s_, colr) in _TAGS[col]:
        if t < t0 or t > t1 + 0.4:
            continue
        a = fade(t, t0, 0.25) * out_fade(t, t1, 0.35)
        tag(ctx, s_, COLS[col]["cx"] + XOFF[col](t), TAG_Y, 40, colr, a, prog(t, t0, s_, 12))


def height_mark(ctx, col, z, label, t0, t, a=1.0, side=1, size=36, dashed=False, dy=0.0):
    """体の前に、濡れる高さの赤い線（地面からの高さ z m）と札"""
    if t < t0 or a <= 0.003:
        return
    cx = COLS[col]["cx"]
    y = GY - z * K
    p = clamp01((t - t0) / 0.45)
    ctx.save()
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.set_line_width(5 if not dashed else 3.5)
    if dashed:
        ctx.set_dash([10, 7])
    ctx.move_to(cx - 26, y)
    ctx.line_to(cx - 26 + 90 * p, y)
    ctx.stroke()
    ctx.set_dash([])
    if not dashed:                                                # 地面からの寸法線
        xm = cx + 76
        ctx.set_line_width(3)
        ctx.move_to(xm, GY)
        ctx.line_to(xm, GY - (GY - y) * p)
        ctx.stroke()
        for yy in (GY, y):
            ctx.move_to(xm - 8, yy)
            ctx.line_to(xm + 8, yy)
        ctx.stroke()
    ctx.restore()
    tag(ctx, label, cx + side * 122, y + dy, size, RED, a * fade(t, t0 + 0.3, 0.25), prog(t, t0 + 0.3, label, 12))


def angle_mark(ctx, col, t0, t, a=1.0):
    """雨の傾き（鉛直からの角度）を、体の前の空中に分度器のように描く"""
    if t < t0 or a <= 0.003:
        return
    cx = COLS[col]["cx"]
    vx, vy, L = cx + 140, 462.0, 120.0
    slant = velrel(col, t) / U
    ang = math.degrees(math.atan(abs(slant)))
    p = clamp01((t - t0) / 0.5)
    ctx.save()
    ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
    ctx.set_line_width(3)
    ctx.set_dash([8, 7])
    ctx.move_to(vx, vy)
    ctx.line_to(vx, vy + L * p)
    ctx.stroke()
    ctx.set_dash([])
    nrm = 1 / math.sqrt(1 + slant * slant)
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * a))
    ctx.set_line_width(5)
    ctx.move_to(vx, vy)
    ctx.line_to(vx + slant * L * nrm * p, vy + L * nrm * p)
    ctx.stroke()
    a0, a1 = math.pi / 2, math.atan2(1, slant)
    if abs(a1 - a0) > 0.01:
        ctx.set_line_width(3)
        if a1 > a0:
            ctx.arc(vx, vy, 52, a0, a0 + (a1 - a0) * p)
        else:
            ctx.arc_negative(vx, vy, 52, a0, a0 + (a1 - a0) * p)
        ctx.stroke()
    ctx.restore()
    s_ = f"{ang:.0f}°"
    tag(ctx, s_, vx + 6, vy + L + 38, 40, RED, a * fade(t, t0 + 0.3, 0.25))


def tilt_dial(ctx, col, t, a=1.0):
    """傘の傾きのダイヤル（列の上）。針は傘と同じ向き・同じ色"""
    if a <= 0.003:
        return
    cx = COLS[col]["cx"]
    phi = PHI[col](t)
    y0, Ld = 200.0, 64.0
    ctx.save()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    ctx.set_dash([8, 7])
    ctx.move_to(cx - Ld, y0)
    ctx.line_to(cx + Ld, y0)
    ctx.stroke()
    ctx.set_dash([])
    for deg in range(0, 51, 10):                                   # 目盛り（前の側、0〜50度）
        r_ = math.radians(deg)
        ctx.move_to(cx + (Ld + 6) * math.cos(r_), y0 + (Ld + 6) * math.sin(r_))
        ctx.line_to(cx + (Ld + 16) * math.cos(r_), y0 + (Ld + 16) * math.sin(r_))
    ctx.stroke()
    ph = math.radians(phi)
    ctx.set_source_rgba(*hexrgb(UMB_COL[col], a))
    ctx.set_line_width(8)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(cx - Ld * math.cos(ph), y0 - Ld * math.sin(ph))
    ctx.line_to(cx + Ld * math.cos(ph), y0 + Ld * math.sin(ph))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.arc(cx, y0, 6, 0, 2 * math.pi)
    ctx.fill()
    if ph > 0.01:
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))
        ctx.set_line_width(3)
        ctx.arc(cx, y0, 44, 0, ph)
        ctx.stroke()
    ctx.restore()
    text(ctx, f"傾き {phi:.0f}°" if phi > -0.5 else f"後ろへ {-phi:.0f}°", cx, 130, 40, RED if abs(phi) > 0.5 else INK, alpha=a)


def size_icons(ctx, t, a=1.0):
    """3つの傘の大きさ（左ページの上）。いまの大きさを赤ペンで囲む"""
    if a <= 0.003:
        return
    items = ((UMBRELLAS["折りたたみ傘"][0], "折りたたみ傘", "90cm", 230.0), (DU, "長傘", "1m", 505.0),
             (UMBRELLAS["ゴルフ傘"][0], "大きな傘", "1m20cm", 780.0))
    kk = 110.0
    cur = DU_T(t)
    for i, (du, name, lab, x) in enumerate(items):
        draw_umbrella(ctx, x, 190 + HU * kk, du, 0.0, CROWD_UMB, 1.0, a, k=kk, lw=2.5, part="canopy")
        text(ctx, name, x, 118, 28, PENCIL, bold=False, alpha=a)
        text(ctx, lab, x, 232, 32, INK, alpha=a)
        near = clamp01(1 - abs(cur - du) / 0.05)
        if near > 0.01:
            pen_circle(ctx, x, 208, 100, 50, RED, seed=40 + i, width=5, alpha=a * near)


def wind_banner(ctx, t, a=1.0):
    """風の向きと強さ（左ページの上）"""
    if a <= 0.003:
        return
    w = WIND_T(t)
    s_ = "風 秒速3m" if abs(w) < 0.5 else ("追い風 秒速3m" if w > 0 else "向かい風 秒速3m")
    text(ctx, s_, 505, 112, 44, SKY, alpha=a)
    if abs(w) > 0.05:
        sg = 1 if w > 0 else -1
        L = 150 * min(1.0, abs(w) / WIND)
        pen_arrow(ctx, 505 - sg * L, 165, 505 + sg * L, 165, SKY, seed=7 if sg > 0 else 9, width=7, alpha=a, head=26)


# ---------- 1万人（左ページの上に、傘をさした小さな人が速い順に並ぶ） ----------
CROWD_N = 16
_ND = np.load(OUT / "data.npz")
_vs_sorted = np.sort(_ND["vs"])
CROWD_V = [float(_vs_sorted[int((i + 0.5) / CROWD_N * N_PEOPLE)]) for i in range(CROWD_N)]
CROWD_H = 95.0
CROWD_POS = [(160.0 + (i // 2) * 98.0, 222.0 if i % 2 == 0 else 365.0, v) for i, v in enumerate(CROWD_V)]
CROWD_RANK = np.argsort(np.random.default_rng(31).permutation(CROWD_N))


def z_dry_flat(v, du=DU):
    """傘水平・無風で、体の中心線の前が濡れる高さ（解析式。照合 B4 と同じ式）"""
    return max(0.0, min(BH, HU - (du / 2 - BL / 2) * U / v))


def T_C0():
    return S("g2b") + 0.7


def draw_crowd(ctx, t, a=1.0):
    if a <= 0.003:
        return
    k = CROWD_H / BH
    for i, (x, gy, v) in enumerate(CROWD_POS):
        ti = T_C0() + 0.27 * CROWD_RANK[i]
        ai = fade(t, ti, 0.3) * a
        if ai <= 0.003:
            continue
        run = v > 2.6
        phase = 2 * math.pi * (3.0 if run else 1.6) * t + i
        draw_umbrella(ctx, x, gy, DU, 0.0, CROWD_UMB, 1.0, ai, k=k, lw=2.0, part="handle")
        ctx.push_group()
        draw_person(ctx, x, gy, CROWD_H, CROWD_COL, phase, run, 1.0, 1.0, grip_point(x, gy, 0.0, k))
        wz = z_dry_flat(v) * clamp01((t - ti - 0.25) / 0.6)
        if wz > 0.005:
            ctx.save()
            ctx.set_operator(cairo.OPERATOR_ATOP)
            ctx.set_source_rgba(*hexrgb(ORANGE, 0.92))
            ctx.rectangle(x - 4, gy - wz * k, 24, wz * k + 4)
            ctx.fill()
            ctx.restore()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(ai)
        draw_umbrella(ctx, x, gy, DU, 0.0, CROWD_UMB, 1.0, ai, k=k, lw=2.0, part="canopy")
    la = a * fade(t, T_C0() + 0.5, 0.4)
    text(ctx, "ゆっくり", 128, 396, 28, PENCIL, align="left", bold=False, alpha=la)
    text(ctx, "速い", 884, 396, 28, PENCIL, align="right", bold=False, alpha=la)
    pen_arrow(ctx, 260, 396, 820, 396, PENCIL, seed=17, width=3, alpha=0.6 * la, head=14)


def L_street(ctx, t):
    """左ページ全体（どの章でも、雨の道と2人と傘がいる）"""
    idx = tl.chapter_at(t)[0] if tl.chapter_at(t) else 0
    for col in COLS:
        draw_column(ctx, t, col)
    # 列の境目（鉛筆の点線）
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.35))
    ctx.set_line_width(2)
    ctx.set_dash([6, 9])
    ctx.move_to(505, RAIN_TOP + 10)
    ctx.line_to(505, GY + 60)
    ctx.stroke()
    ctx.set_dash([])
    # 0章: 大きく「雨」（0秒目から）。着地でもう一度
    ta = out_fade(t, S("ch1") - 0.2, 0.4) + fade(t, S("c8_1"), 0.5)
    if ta > 0.003:
        text(ctx, "雨", 505, 158, 150, INK, alpha=min(1.0, ta))
        t_ul = 0.0 if t < S("ch1") else S("c8_1") + 0.2
        pen_line(ctx, 440, 240, 570, 236, RED, seed=3, width=9, progress=clamp01((t - t_ul) / 0.6), alpha=min(1.0, ta))
    # 1万人
    ca = fade(t, T_C0() - 0.3, 0.3) * out_fade(t, S("ch2") - 0.35, 0.35)
    draw_crowd(ctx, t, ca)
    # 名札（付箋）
    for col in COLS:
        a = sticky_alpha(col, t)
        if a > 0.003:
            st_ = sticky_text(col, t)
            sticky(ctx, st_, COLS[col]["cx"], sticky_y(t), 40, LABEL[col][1], a=a,
                   tilt=-0.03 if col == "walk" else 0.025)
        draw_tags(ctx, t, col)
        draw_meter(ctx, t, col)
    # 0章: 傘の寸法線（歩く人の傘に）
    da = fade(t, S("c1_1") + 0.3, 0.4) * out_fade(t, S("ch1") - 0.3, 0.3)
    if da > 0.003:
        cx = COLS["walk"]["cx"]
        yc = GY - HU * K
        p = clamp01((t - S("c1_1") - 0.3) / 0.6)
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * da))
        ctx.set_line_width(3)
        yd = yc - 34
        ctx.move_to(cx - 90, yd)
        ctx.line_to(cx - 90 + 180 * p, yd)
        xv = cx - 126
        ctx.move_to(xv, GY)
        ctx.line_to(xv, GY - (GY - yc) * p)
        for (xa, ya, xb, yb) in ((cx - 90, yd - 9, cx - 90, yd + 9), (cx + 90, yd - 9, cx + 90, yd + 9),
                                 (xv - 9, GY, xv + 9, GY), (xv - 9, yc, xv + 9, yc)):
            ctx.move_to(xa, ya)
            ctx.line_to(xb, yb)
        ctx.stroke()
        text(ctx, "1m", cx - 104, yd, 30, RED, align="right", alpha=da * p)
        text(ctx, "1.9m", xv - 12, (GY + yc) / 2, 30, RED, align="right", alpha=da * p)
    # 3章: 雨の傾き・濡れる高さ
    if idx == CH_WHY or (idx == CH_TILT and t < S("ch3") + 0.4):
        aw = out_fade(t, S("ch3") - 0.3, 0.35)
        am = aw * out_fade(t, S("c3_7") - 0.2, 0.35)
        for col in COLS:
            angle_mark(ctx, col, S("c3_4") + (0.2 if col == "walk" else 0.55 * dur("c3_4")), t, am)
        height_mark(ctx, "walk", RES["ch2"]["1.4"]["umb"]["z_dry_edge"], "40cm", S("c3_7") + 0.6 * dur("c3_7"), t,
                    aw, side=1)
        height_mark(ctx, "run", RES["ch2"]["5.0"]["umb"]["z_dry_center"], "約140cm", S("c3_8") + 0.3 * dur("c3_8"), t,
                    aw, side=-1)
    # 4章: 傾きのダイヤル・傾けても濡れる高さ
    da = fade(t, S("ch3") + 0.4, 0.4) * out_fade(t, S("ch4") - 0.3, 0.35)
    if da > 0.003:
        for col in COLS:
            tilt_dial(ctx, col, t, da)
        zr = ARM_CALM["run"]
        height_mark(ctx, "run", (zr["z_dry_center"] + zr["z_dry_edge"]) / 2, "約30cm", mid("c4_7", 0.45), t, da, side=-1)
    # 5章: 傘の大きさ
    size_icons(ctx, t, fade(t, S("ch4") + 0.4, 0.4) * out_fade(t, S("ch5") - 0.3, 0.35))
    # 6章: 風
    wa = fade(t, S("c6_2") + 0.3, 0.4) * out_fade(t, S("ch6") - 0.3, 0.35)
    wind_banner(ctx, t, wa)
    # 7章: モデルの決めごと（人は箱・傘は円板）
    ma = fade(t, S("c7_7"), 0.4) * out_fade(t, S("c8_1") - 0.2, 0.4)
    if ma > 0.003:
        for col in COLS:
            cx = COLS[col]["cx"]
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.9 * ma))
            ctx.set_line_width(3)
            ctx.set_dash([9, 7])
            ctx.rectangle(cx - BL / 2 * K, GY - FIG_H, BL * K, FIG_H)
            ctx.stroke()
            ctx.set_dash([])
            text(ctx, "円板", cx - 132, GY - HU * K, 30, PENCIL, alpha=ma)
        mb = fade(t, S("c7_7b"), 0.4) * ma
        for col in COLS:
            text(ctx, "箱", COLS[col]["cx"] - 52, GY - FIG_H / 2, 30, PENCIL, alpha=mb)


def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 1010)
    ctx.clip()


# ============================================================
# 右ページ（手書きの見出し・式・表・散布図）
# ============================================================
def rule_no(ctx, i, x, y, t0, t, a=1.0):
    """①②③ の丸数字（ペンで丸を描いて数字）"""
    if t >= t0:
        pen_circle(ctx, x, y, 27, 27, INK, seed=60 + i, width=4, progress=clamp01((t - t0) / 0.3), alpha=a)
        text(ctx, str(i + 1), x, y, 34, INK, alpha=a * fade(t, t0 + 0.1, 0.2))


def R_open(ctx, t):
    tc1 = S("c1_1")
    a = out_fade(t, tc1 - 0.15, 0.4)
    if a > 0:
        rules = (("c0_1", "100m 進む", 200), ("c0_2", "雨 1時間に10mm", 300), ("c0_3", "粒 2mm・秒速6.5m", 410))
        for i, (cid, s_, y) in enumerate(rules):
            t0 = S(cid) + 0.3
            rule_no(ctx, i, RX + 26, y, t0, t, a)
            wr(ctx, s_, RX + 78, y, 46, INK, t0 + 0.15, t, alpha=a)
        wr(ctx, "傘がいる強さ", RX + 78, 354, 32, PENCIL, mid("c0_2", 0.6), t, alpha=a)
        wr(ctx, "まっすぐ落ちる", RX + 78, 464, 32, PENCIL, mid("c0_3", 0.75), t, alpha=a)
        wr(ctx, "まず、傘なしで比べる", RX, 560, 36, INK, S("c0_6") + 0.2, t, alpha=a)
        c1 = RES["ch1"]
        wr(ctx, f"歩く 約{fmt(r100(c1['walk_plain']))}粒 ／ 走る 約{fmt(r100(c1['run_plain']))}粒", RX, 625, 36, INK,
           S("c0_7") + 0.2, t, alpha=a, cps=14)
    if t >= tc1:
        t0 = tc1 + 0.15
        wr(ctx, "傘があっても、", RX, 170, 52, INK, t0, t, cps=10)
        s2 = "走るほうが濡れない？"
        wr(ctx, s2, RX, 236, 52, INK, t0 + 0.6, t, cps=10)
        t3 = S("c1_3")
        if t >= t3:
            pen_line(ctx, RX - 4, 274, RX + text_width(s2, 52) + 6, 270, RED, seed=5, width=7,
                     progress=clamp01((t - t3 - 0.3) / 0.5))
        wr(ctx, "傘 直径1m・高さ1.9m", RX, 345, 44, INK, tc1 + 0.4, t, cps=11)
        t2 = S("c1_2")
        wr(ctx, "上からの雨 → 傘が防ぐ", RX, 440, 40, INK, t2 + 0.2, t)
        wr(ctx, "あとは、雨の中にいる時間が短いほうが得？", RX, 505, 34, INK, mid("c1_2", 0.5), t, cps=12)
        wr(ctx, "→ 傘があっても、走るほうが濡れない？", RX, 600, 40, RED, S("c1_3") + 0.3, t, cps=12)


# ---------- 散布図（ショートの散布図をコピー。速さは時速で目盛る） ----------
PX0, PX1, PY0, PY1 = 1150.0, 1770.0, 195.0, 595.0
VMIN, VMAX = 0.8, 7.2
YMAX = 16000.0
VS_ALL = _ND["vs"]
H_PLAIN = _ND["h_plain_calm"]
H_UMB = _ND["h_flat_calm"]
_PERM = np.random.default_rng(11).permutation(N_PEOPLE)
_OFFS = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if dx * dx + dy * dy <= 5]
SRX0, SRY0 = int(PX0) - 12, int(PY0) - 30
SRW, SRH = int(PX1 - PX0) + 24, int(PY1 - PY0) + 44


def sx(v):
    return PX0 + (np.asarray(v, dtype=float) - VMIN) / (VMAX - VMIN) * (PX1 - PX0)


def sy(h):
    return PY1 - np.asarray(h, dtype=float) / YMAX * (PY1 - PY0)


def raster_dots(xs, ys, col, alpha=0.42):
    """点を重ねて塗った画像（紙の上なので、重なるほど濃くなる）"""
    ix = np.round(xs - SRX0).astype(np.int64)
    iy = np.round(ys - SRY0).astype(np.int64)
    cov = np.zeros(SRW * SRH)
    for dx, dy in _OFFS:
        x2, y2 = ix + dx, iy + dy
        ok = (x2 >= 0) & (x2 < SRW) & (y2 >= 0) & (y2 < SRH)
        cov += np.bincount((y2 * SRW + x2)[ok], minlength=SRW * SRH)
    al = 1 - (1 - alpha) ** cov
    c = hexrgb(col)
    out = np.zeros((SRH, SRW, 4), np.uint8)
    for ch, kk in ((2, 0), (1, 1), (0, 2)):
        out[:, :, kk] = (c[ch] * al * 255).reshape(SRH, SRW).astype(np.uint8)
    out[:, :, 3] = (al * 255).reshape(SRH, SRW).astype(np.uint8)
    out = np.ascontiguousarray(out)
    return cairo.ImageSurface.create_for_data(memoryview(out), cairo.FORMAT_ARGB32, SRW, SRH, SRW * 4), out


_DOT_CACHE = {}


def paint_dots(ctx, which, k, a):
    k = int(k)
    if k <= 0 or a <= 0.003:
        return
    key = (which, k)
    if key not in _DOT_CACHE:
        if len(_DOT_CACHE) > 6:
            _DOT_CACHE.clear()
        idx = _PERM[:k]
        h = H_PLAIN if which == "p" else H_UMB
        _DOT_CACHE[key] = raster_dots(sx(VS_ALL[idx]), sy(h[idx]), PUR if which == "p" else ORG)
    ctx.set_source_surface(_DOT_CACHE[key][0], SRX0, SRY0)
    ctx.paint_with_alpha(a)


def T_D0():
    return S("g2b") + 0.5


def T_D1():
    return E("g2b") - 0.5


def n_people(t):
    return int(N_PEOPLE * clamp01((t - T_D0()) / (T_D1() - T_D0())))


def draw_axes(ctx, a):
    if a <= 0.003:
        return
    pen_line(ctx, PX0 - 6, PY0 - 10, PX0 - 6, PY1 + 3, INK, seed=3, width=4.5, alpha=0.85 * a)
    pen_line(ctx, PX0 - 6, PY1 + 3, PX1 + 10, PY1 + 3, INK, seed=4, width=4.5, alpha=0.85 * a)
    for val, lab in ((0, "0"), (5000, "5千"), (10000, "1万"), (15000, "1.5万")):
        yy = float(sy(val))
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(PX0 - 14, yy)
        ctx.line_to(PX0 - 6, yy)
        ctx.stroke()
        text(ctx, lab, PX0 - 20, yy, 28, INK, align="right", bold=False, alpha=a)
    for kmh in (5, 10, 15, 20, 25):
        xx = float(sx(kmh / 3.6))
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(3)
        ctx.move_to(xx, PY1 + 3)
        ctx.line_to(xx, PY1 + 12)
        ctx.stroke()
        text(ctx, str(kmh), xx, PY1 + 34, 28, INK, alpha=a)
    text(ctx, "進む速さ（時速km）", (PX0 + PX1) / 2, PY1 + 74, 30, INK, bold=False, alpha=a)
    text(ctx, "当たった雨粒（粒）", PX0 - 80, PY0 - 34, 28, INK, align="left", bold=False, alpha=a)


def _curve(key):
    pts = [(c["v"], c[key]) for c in RES["ch1"]["curve"] if V_LO - 1e-9 <= c["v"] <= V_HI + 1e-9]
    return [(float(sx(v)), float(sy(h))) for v, h in pts]


CURVE_P, CURVE_U = _curve("plain"), _curve("umb")


def pen_poly(ctx, pts, col, width, p, a):
    n = max(2, int(len(pts) * clamp01(p)))
    if p <= 0 or a <= 0.003:
        return
    ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for q in pts[1:n]:
        ctx.line_to(*q)
    ctx.stroke()


def draw_scatter(ctx, t, a):
    if a <= 0.003:
        return
    draw_axes(ctx, a)
    k = n_people(t)
    paint_dots(ctx, "p", k, a)
    paint_dots(ctx, "u", k, a)
    if t < T_D1() + 0.3:
        b = a * out_fade(t, T_D1() + 0.2, 0.3)
        text(ctx, f"ためした人 {fmt(k)} ／ 10,000人", 1430, 112, 30, INK, alpha=b)
    else:
        legend_at(ctx, [(PUR, "傘なし"), (ORG, "傘あり")], 1560, 112, a=a * fade(t, T_D1() + 0.3, 0.3))
    t7 = S("c2_7")
    if t >= t7:
        pen_poly(ctx, CURVE_P, "#4a3590", 5, (t - t7 - 0.2) / 1.0, a)
        pen_poly(ctx, CURVE_U, "#b5600c", 5, (t - mid("c2_7", 0.45)) / 1.0, a)
        wr(ctx, "傘なし ↘", float(sx(V_RUN)), float(sy(RES["ch1"]["run_plain"])) - 40, 34, "#4a3590", t7 + 0.4, t,
           align="center", alpha=a)
        wr(ctx, "傘あり ↗", float(sx(V_RUN)), float(sy(RES["ch1"]["run_umb"])) + 44, 34, "#b5600c", mid("c2_7", 0.5), t,
           align="center", alpha=a)
    t8 = S("c2_8b")
    if t >= t8:
        vz = RES["ch1"]["zero"][0][1]
        cxz = float(sx((V_LO + vz) / 2))
        pen_circle(ctx, cxz, PY1 - 6, 34, 22, RED, seed=71, width=5, progress=clamp01((t - t8) / 0.5), alpha=a)
        s_ = "時速4km以下 → ほぼ0粒"
        wr(ctx, s_, 1600, 236, 34, RED, t8 + 0.3, t, align="center", alpha=a)
        if t >= t8 + 0.5:
            pen_arrow(ctx, 1450, 262, cxz + 22, PY1 - 30, RED, seed=33, width=4, alpha=a * fade(t, t8 + 0.5, 0.3), head=18)


def R_umb(ctx, t):
    a = out_fade(t, S("c2_6") - 0.1, 0.4)
    if a > 0.003:
        c1 = RES["ch1"]
        wr(ctx, "傘をさして 100m", RX, 165, 52, INK, S("ch1") + 0.4, t, cps=10, alpha=a)
        wr(ctx, "歩く人", RX, 265, 40, INK, S("c2_2") + 0.1, t, alpha=a)
        wr(ctx, f"約{fmt(r100(c1['walk_umb']))}粒", RX + 170, 265, 56, INK, S("c2_2") + 0.4, t, alpha=a)
        wr(ctx, "走る人", RX, 355, 40, INK, S("c2_3") + 0.1, t, alpha=a)
        wr(ctx, f"約{fmt(r100(c1['run_umb']))}粒", RX + 170, 355, 56, RED, S("c2_3") + 0.4, t, alpha=a)
        wr(ctx, "逆転！", RX, 455, 64, RED, mid("c2_4", 0.75), t, cps=8, alpha=a)
        wr(ctx, "傘あり歩き ≒ 傘なし走りの 1割ちょっと", RX, 560, 36, INK, S("c2_5") + 0.4, t, cps=12, alpha=a)
    sa = fade(t, S("c2_6b") - 0.2, 0.4)
    draw_scatter(ctx, t, sa)


def R_why(ctx, t):
    wr(ctx, "なぜ？", RX, 160, 60, INK, S("ch2") + 0.4, t, cps=8)
    wr(ctx, "止まる → 雨は真上から", RX, 245, 38, INK, S("c3_2") + 0.3, t)
    wr(ctx, "進む → 雨は前から斜めに", RX, 310, 38, INK, S("c3_3") + 0.3, t)
    t4 = S("c3_4")
    wr(ctx, "雨の傾き", RX, 390, 38, INK, t4 + 0.2, t)
    a12 = apparent_angle(V_WALK)
    a38 = apparent_angle(V_RUN)
    wr(ctx, f"歩く {a12:.0f}°", RX + 190, 390, 44, INK, t4 + 0.3 * dur("c3_4"), t)
    wr(ctx, f"走る {a38:.0f}°", RX + 410, 390, 44, RED, t4 + 0.7 * dur("c3_4"), t)
    wr(ctx, "→ 傘の影が 後ろへずれる", RX, 465, 38, INK, S("c3_5") + 0.4, t)
    wr(ctx, "はみ出す高さ", RX, 540, 36, INK, S("c3_7") + 0.3, t)
    wr(ctx, "歩く 40cm", RX + 230, 540, 40, INK, mid("c3_7", 0.6), t)
    wr(ctx, "走る 約140cm", RX + 460, 540, 40, RED, S("c3_8") + 0.4, t)
    t9 = S("c3_9")
    wr(ctx, f"前から当たる雨　傘なし: 約{fmt(r100(RES['ch1']['floor']))}粒（速さに関係ない）", RX, 615, 32, INK, t9 + 0.3, t, cps=14)
    wr(ctx, "傘あり: 速いほど増える", RX + 256, 665, 32, RED, S("c3_10") + 0.4, t, cps=12)


def inset_rainview(ctx, t, a, center=None):
    """雨の向きから見た図: 傘（雨に垂直に向けると円）と、体の影絵。体の下が円からはみ出す。
    center は円板の中心（前へ m, 高さ m）。4章（改）の走る人の一番いい置き方（前へ70cm・高さ1.82m）"""
    if a <= 0.003:
        return
    th = math.radians(apparent_angle(V_RUN))
    e = (math.cos(th), -math.sin(th))          # 雨に垂直な向き（前の下がり）。x→前、z→上
    def proj(x, z):
        return x * e[0] + z * e[1]
    body = [proj(x, z) for x in (-BL / 2, BL / 2) for z in (0.0, BH)]
    pb0, pb1 = min(body), max(body)
    ccx, ccz = center if center else (0.0, HU)
    pc = proj(ccx, ccz)
    R = DU / 2
    kk = 128.0
    lo = min(pc - R, pb0)
    X0, Y0 = 1240.0, 505.0
    def Y(p):
        return Y0 + (p - lo) * kk
    ctx.save()
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, RX - 10, 458, 770, 218, 14)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * a))
    ctx.set_line_width(2.5)
    rrect(ctx, RX - 10, 458, 770, 218, 14)
    ctx.stroke()
    bw = BW * kk
    ctx.set_source_rgba(*hexrgb(RUN_COL, a))
    ctx.rectangle(X0 - bw / 2, Y(pb0), bw, (pb1 - pb0) * kk)
    ctx.fill()
    ctx.save()
    ctx.rectangle(X0 - bw / 2, Y(pb0), bw, (pb1 - pb0) * kk)
    ctx.clip()
    ctx.rectangle(0, 0, lf.W, lf.H)
    ctx.arc(X0, Y(pc), R * kk, 0, 2 * math.pi)
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    ctx.set_source_rgba(*hexrgb(ORANGE, 0.9 * a))
    ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3)
    ctx.rectangle(X0 - bw / 2, Y(pb0), bw, (pb1 - pb0) * kk)
    ctx.stroke()
    ctx.arc(X0, Y(pc), R * kk, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(RED, 0.35 * a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.set_line_width(4)
    ctx.stroke()
    ctx.restore()
    text(ctx, "雨の来る方向から見ると", RX + 10, 482, 28, PENCIL, align="left", bold=False, alpha=a)
    text(ctx, "傘（直径1m）", X0 + R * kk + 18, Y(pc) - 12, 34, RED, align="left", alpha=a)
    yb = Y(pc + R)
    text(ctx, "体", X0 - bw / 2 - 14, Y(pc), 30, INK, align="right", alpha=a)
    pen_line(ctx, X0 + bw / 2 + 14, yb + 4, X0 + bw / 2 + 14, Y(pb1) - 2, ORANGE, seed=91, width=6, alpha=a)
    text(ctx, "← はみ出す（足元）", X0 + bw / 2 + 30, (yb + Y(pb1)) / 2 + 4, 30, "#c06a10", align="left", alpha=a)


def R_tilt(ctx, t):
    wr(ctx, "腕の届く範囲（肩から60cm）で探す", RX, 160, 38, INK, mid("c4_2b", 0.15), t, cps=12)
    wr(ctx, "一番効く傾き ＝ 雨の傾き", RX, 222, 46, RED, S("c4_3") + 0.3, t, cps=10)
    c1 = RES["ch1"]
    cols = (RX, RX + 150, RX + 300, RX + 475, RX + 660)
    th = S("c4_4")
    if t >= th:
        ha = fade(t, th, 0.3)
        for x, s_ in zip(cols[1:], ("傾き", "傘の位置", "まっすぐ", "前に出して傾ける")):
            text(ctx, s_, x, 282, 26, PENCIL, bold=False, alpha=ha)
    rows = (("c4_4", "歩く", "walk", c1["walk_umb"], INK, mid("c4_4", 0.7)),
            ("c4_5", "走る", "run", c1["run_umb"], RED, mid("c4_6", 0.45)))
    for i, (cid, nm, col, e0, colr, t1) in enumerate(rows):
        y = 332 + 55 * i
        t0 = S(cid) + 0.1
        if t < t0:
            continue
        a_ = ARM_CALM[col]
        wr(ctx, nm, cols[0], y, 38, colr, t0, t)
        text(ctx, f"{a_['phi']:.0f}°", cols[1], y, 38, colr, alpha=fade(t, t0 + 0.3, 0.3))
        text(ctx, f"前へ{a_['cx'] * 100:.0f}cm", cols[2], y, 34, colr, alpha=fade(t, t0 + 0.6 * dur(cid), 0.3))
        text(ctx, f"約{fmt(r100(e0))}", cols[3], y, 38, INK, alpha=fade(t, t1 - 0.6 if i else t0 + 0.4, 0.3))
        if t >= t1:
            v_ = r100(a_["e"])
            text(ctx, f"約{fmt(v_)}" if v_ > 0 else "0", cols[4], y, 40, colr, alpha=fade(t, t1, 0.3))
    t5 = mid("c4_6", 0.75)
    if t >= t5:
        pen_circle(ctx, cols[4], 387, 82, 28, RED, seed=55, width=5, progress=clamp01((t - t5) / 0.5))
        text(ctx, "→ 3分の1以下", cols[4], 430, 30, RED, alpha=fade(t, t5 + 0.2, 0.3))
    inset_rainview(ctx, t, fade(t, S("c4_8"), 0.4), center=(ARM_CALM["run"]["cx"], ARM_CALM["run"]["hu"]))


def R_size(ctx, t):
    c4 = RES["ch4"]["umbrellas"]
    xs = (RX, RX + 305, RX + 455, RX + 665)
    t0 = S("ch4") + 0.4
    if t >= t0:
        for x, s_ in zip(xs[1:], ("直径", "歩く", "走る")):
            text(ctx, s_, x, 165, 30, PENCIL, bold=False, alpha=fade(t, t0, 0.3))
    rows = (("c5_2", "折りたたみ傘", "90cm", c4["折りたたみ傘"], 245),
            ("ch4", "長傘", "1m", c4["長傘"], 315),
            ("c5_3", "大きな傘", "1m20cm", c4["ゴルフ傘"], 385))
    for cid, nm, dia, e, y in rows:
        ts = S(cid) + (0.5 if cid == "ch4" else 0.2)
        if t < ts:
            continue
        a = fade(t, ts, 0.3)
        text(ctx, nm, xs[0], y, 36, INK, align="left", alpha=a)
        text(ctx, dia, xs[1], y, 40, INK, alpha=a)
        w_ = r100(e["walk"]["flat"])
        sw = f"約{fmt(w_)}" if w_ > 0 else "0"
        tw = ts + (0.35 * dur(cid) if cid != "ch4" else 0.3)
        tr = ts + (0.65 * dur(cid) if cid != "ch4" else 0.6)
        text(ctx, sw, xs[2], y, 40, INK, alpha=fade(t, tw, 0.3))
        text(ctx, f"約{fmt(r100(e['run']['flat']))}", xs[3], y, 40, RED, alpha=fade(t, tr, 0.3))
        if w_ == 0 and t >= tw + 0.4:
            pen_circle(ctx, xs[2], y, 34, 30, RED, seed=66, width=5, progress=clamp01((t - tw - 0.4) / 0.5))
    t5 = S("c5_5") + 0.3
    if t >= t5:
        pen_circle(ctx, xs[3], 315, 114, 122, RED, seed=67, width=5, progress=clamp01((t - t5) / 0.6))
    wr(ctx, "大きい傘ほど、差が広がる", RX, 520, 48, RED, S("c5_6") + 0.3, t, cps=10)
    wr(ctx, "まっすぐなら 走る人の濡れは 速さで決まる", RX, 610, 36, INK, mid("c5_7b", 0.4), t, cps=12)


def R_wind(ctx, t):
    c5 = RES["ch5"]
    tr5 = {r["v"]: r for r in c5["tail"]["rows"]}
    hr5 = {r["v"]: r for r in c5["head"]["rows"]}
    wr(ctx, "風 秒速3m（雨も横に秒速3m）", RX, 160, 40, INK, S("c6_2") + 0.3, t, cps=11)
    xw, xr = RX + 440, RX + 660
    if t >= S("c6_4"):
        ha = fade(t, S("c6_4"), 0.3)
        text(ctx, "歩く", xw, 232, 30, PENCIL, bold=False, alpha=ha)
        text(ctx, "走る", xr, 232, 30, PENCIL, bold=False, alpha=ha)
    rows = (("c6_4", "追い風・まっすぐ", tr5[V_WALK]["flat"], tr5[V_RUN]["flat"], 285),
            ("c6_5n", "向かい風・まっすぐ", hr5[V_WALK]["flat"], hr5[V_RUN]["flat"], 340),
            ("c6_9", "追い風・雨に向ける", ARM_TAIL["walk"]["e"], ARM_TAIL["run"]["e"], 425),
            ("c6_10", "向かい風・雨に向ける", ARM_HEAD["walk"]["e"], ARM_HEAD["run"]["e"], 530))
    for cid, lab, ew, er, y in rows:
        t0 = S(cid) + 0.1
        if t < t0:
            continue
        wr(ctx, lab, RX, y, 34, INK, t0, t, cps=12)
        for x, e_, f_ in ((xw, ew, 0.35), (xr, er, 0.7)):
            tt = mid(cid, f_ if cid != "c6_9" else 0.3 + 0.3 * (x == xr))
            v_ = r100(e_)
            if t >= tt:
                text(ctx, f"約{fmt(v_)}" if v_ > 0 else "0", x, y, 40, INK if x == xw else RED, alpha=fade(t, tt, 0.3))
    t6 = S("c6_6") + 0.3
    if t >= t6:
        pen_circle(ctx, xr + 18, 312, 132, 62, RED, seed=84, width=5, progress=clamp01((t - t6) / 0.5))
    tb = S("c6_8b") + 0.2
    if t >= tb:
        aw, ar = ARM_TAIL["walk"]["phi"], ARM_TAIL["run"]["phi"]
        wr(ctx, f"（追い風: 歩く人は後ろへ{abs(aw):.0f}°、走る人は前へ{ar:.0f}°）", RX, 470, 26, PENCIL, tb, t, cps=14, bold=False)
    t9 = mid("c6_9", 0.75)
    if t >= t9:
        pen_circle(ctx, (xw + xr) / 2, 425, 180, 25, RED, seed=85, width=5, progress=clamp01((t - t9) / 0.5))
    if t >= S("c6_10b"):
        wr(ctx, "（前に出しても 0にはならない）", RX, 570, 28, PENCIL, S("c6_10b") + 0.2, t, cps=14, bold=False)
    wr(ctx, "風の日 → 傘を雨に向ける", RX, 640, 46, RED, S("c6_11") + 0.3 * dur("c6_11"), t, cps=10)


def R_end(ctx, t):
    a = out_fade(t, S("c7_6") - 0.1, 0.4)
    if a > 0.003:
        wr(ctx, "答えは、傘を持っているかで 逆", RX, 165, 44, INK, S("ch6") + 0.4, t, cps=11, alpha=a)
        wr(ctx, "傘なし → 走る（約3割減）", RX, 245, 42, INK, S("c7_2") + 0.2, t, alpha=a)
        wr(ctx, "傘あり → 歩く（走ると約6倍）", RX, 315, 42, RED, S("c7_3") + 0.2, t, alpha=a)
        wr(ctx, f"雨に向けて前に出す: 歩く 0粒／走る 約{fmt(r100(ARM_CALM['run']['e']))}粒", RX, 395, 30, INK,
           S("c7_4") + 0.3, t, cps=13, alpha=a)
        wr(ctx, "風があると: まっすぐなら 走るほうが少ない", RX, 465, 32, RED, S("c7_5b") + 0.2, t, cps=13, alpha=a)
        wr(ctx, "雨に向ければ: 追い風 0粒・向かい風 ほぼ同じ", RX, 525, 32, INK, S("c7_5c") + 0.3, t, cps=13, alpha=a)
    b = fade(t, S("c7_6"), 0.4) * out_fade(t, S("c8_1") - 0.1, 0.4)
    if b > 0.003:
        hu = {r["Hu"]: r for r in RES["ch4"]["hu_sweep"]}
        wr(ctx, "モデルの決めごと", RX, 165, 50, INK, S("c7_6") + 0.3, t, cps=10, alpha=b)
        wr(ctx, "・傘は平らな円板", RX, 250, 34, INK, S("c7_7") + 0.1, t, cps=12, alpha=b)
        wr(ctx, "・人は箱の形、雨粒は全部2mm、風は一定", RX, 310, 34, INK, S("c7_7b") + 0.2, t, cps=12, alpha=b)
        wr(ctx, f"持つ高さ ±10cm → 歩き 約{fmt(r100(hu[1.8]['walk']['flat']))}〜{fmt(r100(hu[2.0]['walk']['flat']))}粒（まっすぐ）",
           RX, 395, 30, INK, mid("c7_8b", 0.3), t, cps=13, alpha=b)
        wr(ctx, "風がなければ、どの傘・どの持ち方でも", RX, 490, 38, INK, S("c7_9") + 0.3, t, cps=11, alpha=b)
        wr(ctx, "「傘ありなら、ゆっくり」", RX, 560, 48, RED, mid("c7_9", 0.5), t, cps=10, alpha=b)
    if t >= S("c8_1"):
        t1 = S("c8_1")
        wr(ctx, "傘があっても、", RX, 170, 52, INK, t1 + 0.2, t, cps=10)
        s2 = "走るほうが濡れない？"
        wr(ctx, s2, RX, 236, 52, INK, t1 + 0.6, t, cps=10)
        t_x = mid("c8_1", 0.75)
        if t >= t_x:
            for k_, y in enumerate((170, 236)):
                w_ = text_width("傘があっても、" if k_ == 0 else s2, 52)
                pen_line(ctx, RX - 4, y + 2, RX + w_ + 4, y - 4, RED, seed=21 + k_, width=6,
                         progress=clamp01((t - t_x - 0.25 * k_) / 0.4))
        wr(ctx, "→ 進むと、雨は前から来る", RX, 350, 48, RED, S("c8_2") + 0.2, t, cps=10)
        wr(ctx, "走るほど 傘の影からはみ出す", RX, 430, 42, INK, mid("c8_2", 0.5), t, cps=11)


# ============================================================
# 右ページ下の「2つの数字」（傘なし: 0章で出し、傘あり: 2章で出して、最後まで出しっぱなし）
# ============================================================
NB = (1030, 712, 1800, 905)
CELLX = (1222, 1608)
LBL_Y, VAL_Y = 752, 835
CUT_TENTHS = int(round(RES["ch1"]["cut_plain"] * 10))
UMB_TIMES = int(round(RES["ch1"]["run_over_walk_umb"]))
NUM1 = f"走ると約{CUT_TENTHS}割減"
NUM2 = f"走ると約{UMB_TIMES}倍"


def T_NUM1():
    return S("c0_7b") + 0.15


def T_NUM2():
    return E("c2_3") + 0.25


def draw_numbers(ctx, t):
    t0 = T_NUM1()
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3)
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.55 * a)
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
    lf.write_on(ctx, "傘なし", CELLX[0], LBL_Y, 34, PENCIL, clamp01((t - t0) / 0.5), align="center", bold=False, alpha=a)
    text(ctx, NUM1, CELLX[0], VAL_Y, fit(NUM1, 60, 330), INK, alpha=a * fade(t, t0 + 0.2, 0.3))
    t2 = T_NUM2()
    if t >= t2 - 0.05:
        b = fade(t, t2, 0.3)
        lf.write_on(ctx, "傘あり", CELLX[1], LBL_Y, 34, PENCIL, clamp01((t - t2) / 0.5), align="center", bold=False, alpha=b)
        text(ctx, NUM2, CELLX[1], VAL_Y, fit(NUM2, 60, 330), RED, alpha=fade(t, t2 + 0.2, 0.3))
    t7 = S("c4_9") + 0.2                                 # 4章: 前に出して傾けても（数字の枠の上に小さく）
    q = fade(t, t7, 0.3) * out_fade(t, S("ch4") - 0.2, 0.35)
    if q > 0.003:
        text(ctx, f"前に出して傾けても 歩く 0／走る 約{fmt(r100(ARM_CALM['run']['e']))}", NB[2], 696, 28, RED, align="right", alpha=q)
    for i, tc in enumerate((S("c7_2") + 0.3, S("c7_3") + 0.3)):     # まとめ: 2つの数字を赤で囲む
        if t >= tc:
            pen_circle(ctx, CELLX[i], VAL_Y - 2, 190, 58, RED, seed=101 + i, width=6, progress=clamp01((t - tc) / 0.5))


# ============================================================
# 付箋・章カード・終了画面・全体
# ============================================================
def overlays(ctx, t, idx):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, CARD_TEXT.get(ch[0], ch[2]), a, size=60)
    tb = S("g2b")                                        # 1万人の合図（亀つき）
    a = fade(t, tb - 0.1, 0.25) * out_fade(t, tb + 1.5, 0.35)
    if a > 0.003:
        note.banner(ctx, "1万人でためす", lf.GUTTER, 470, a=a, t_rel=t - tb)
    tq = S("c8_3") + 0.05
    t5 = S("c8_4")
    if t >= tq:
        a = fade(t, tq, 0.35) * (1 - fade(t, t5 - 0.1, 0.3))
        if a > 0:
            sticky(ctx, "雨の日、あなたは\n傘をどう持っていましたか？", lf.GUTTER, 560, 56, "yellow", a=a, tilt=-0.02)
    if t >= t5:
        from engine.brand import turtle
        a = fade(t, t5 + 0.1, 0.4)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.82 * fade(t, t5 - 0.1, 0.4)))
        ctx.rectangle(0, 0, lf.W, lf.H)
        ctx.fill()
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t5) % 3.2 < 0.45 else 0.0
        turtle(ctx, lf.GUTTER - 5, 545, 0.62, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
        sticky(ctx, "チャンネル登録・高評価 よろしくお願いします", lf.GUTTER, 640, 46, "pink", fg=INK,
               a=fade(t, t5 + 0.3, 0.4), tilt=-0.015)


RIGHTS = [R_open, R_umb, R_why, R_tilt, R_size, R_wind, R_end]


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    ctx.save()
    clip_left(ctx)
    L_street(ctx, t)
    ctx.restore()
    page(ctx, t, RIGHTS, idx, t0)
    draw_numbers(ctx, t)
    overlays(ctx, t, idx)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（雨音・効果音はショートの作り方をコピー。BGM は 0秒から）
# ============================================================
def band_noise(dur_, lo, hi, seed, rms, edge_lo=400.0, edge_hi=1500.0):
    rng = np.random.default_rng(seed)
    n = int(SR * dur_)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / edge_lo, 0, 1) * np.clip((hi - f) / edge_hi, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def rain_sound(dur_, seed=1):
    """うるさくない雨音: 600Hz〜6kHz に絞ったノイズに、ゆっくりした強弱（ショートと同じ）"""
    x = band_noise(dur_, 600.0, 6500.0, seed, 0.030)
    tt = np.arange(len(x)) / SR
    env = 0.8 + 0.2 * np.sin(2 * np.pi * 0.23 * tt + 1.0) * np.sin(2 * np.pi * 0.071 * tt + 0.3)
    fd = np.minimum(1, tt / 0.3) * np.minimum(1, (dur_ - tt) / 0.6)
    return x * env * fd


def wind_sound(dur_, seed=2):
    x = band_noise(dur_, 80.0, 700.0, seed, 0.06, 80.0, 500.0)
    tt = np.arange(len(x)) / SR
    env = np.sin(np.pi * np.clip(tt / dur_, 0, 1)) ** 1.5
    return x * (0.4 + 0.6 * env)


def pop(dur_=0.18):
    """傘がバッと開く音"""
    t_ = _t(dur_)
    n = np.random.default_rng(9).standard_normal(len(t_))
    n = np.convolve(n, np.ones(8) / 8, mode="same")
    return n * np.exp(-t_ * 30) * 1.6 + thump(dur_) * 0.6


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    r = rain_sound(DUR)
    tt = np.arange(len(r)) / SR
    gain = np.where(tt < S("c0_1"), 1.3, 0.8)
    mx.add(0, r * gain, 1.0, bgm=True)
    mx.add(S("c6_2") + 0.4, wind_sound(S("ch6") - S("c6_2")), 0.8, bgm=True)
    for i in range(1, 7):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for cid in ("c0_1", "c0_2", "c0_3"):
        mx.add(S(cid) + 0.3, blip(659.3, 0.12), 0.35)
    for cid in ("c0_4", "c0_5"):
        mx.add(S(cid) + 0.3, blip(784.0, 0.12), 0.3)
    # 早回しで点がたまる音（ショートと同じ作り）
    for run, kinds in ((RUN0, (("run", "run_plain", 2400.0), ("walk", "walk_plain", 1700.0))),
                       (RUN1, (("run", "run_flat", 2400.0), ("walk", "walk_flat", 1700.0)))):
        for col, nm, f0 in kinds:
            lay = layer(nm)
            rng = np.random.default_rng(3 if col == "run" else 4)
            tt0 = run.t0
            while tt0 < run.finish(col):
                n = lay.count(run.tau(tt0 + 0.06)) - lay.count(run.tau(tt0))
                if n > 0:
                    mx.add(tt0, tick(float(rng.uniform(f0, f0 * 1.5)), 0.03), 0.02 + 0.05 * min(1.0, n / 120))
                tt0 += 0.06
        mx.add(run.finish("run"), blip(1046.5, 0.25), 0.4)
        mx.add(run.finish("walk"), blip(784.0, 0.25), 0.4)
    mx.add(T_NUM1() + 0.2, bell(659.3, 1.0), 0.4)
    mx.add(S("c0_8") + 0.25, pop(), 0.5)
    mx.add(S("c0_8") + 0.32, pop(), 0.4)
    mx.add(S("c1_3") + 0.3, blip(523.3, 0.15), 0.3)
    # 2章
    mx.add(S("c2_2") + 0.4, blip(659.3, 0.15), 0.35)
    mx.add(T_NUM2() + 0.2, bell(880.0, 1.4), 0.5)
    mx.add(mid("c2_4", 0.75), chord([261.6, 329.6, 392.0], 1.4), 0.4)
    mx.add(S("g2b") - 0.4, riser(0.9), 0.5)
    beat(mx, T_D0(), T_D1(), bpm=124, vol=0.22, accel=True)
    mx.add(T_D0(), shimmer(400, T_D1() - T_D0(), seed=2), 0.3)
    mx.add(T_D1(), thump(), 0.6)
    mx.add(S("c2_8b") + 0.4, bell(784.0, 1.2), 0.4)
    # 3章
    mx.add(mid("c3_4", 0.3), blip(659.3, 0.12), 0.3)
    mx.add(mid("c3_4", 0.75), blip(784.0, 0.12), 0.3)
    mx.add(mid("c3_7", 0.4), blip(523.3, 0.15), 0.3)
    mx.add(S("c3_8") + 0.4, bell(659.3, 1.0), 0.4)
    mx.add(S("c3_10b") + 0.2, chord([392.0, 493.9, 587.3], 1.2), 0.4)
    # 4章
    mx.add(mid("c4_2b", 0.2), whoosh(0.5), 0.15)
    mx.add(S("c4_3") + 0.2, blip(659.3, 0.12), 0.3)
    mx.add(mid("c4_4", 0.75), bell(784.0, 1.0), 0.35)
    mx.add(S("c4_5") + 0.3, whoosh(0.6), 0.2)
    mx.add(mid("c4_6", 0.45), bell(523.3, 1.0), 0.35)
    mx.add(S("c4_8") + 0.2, whoosh(0.5), 0.2)
    # 5章
    mx.add(S("c5_2") + 0.3, blip(523.3, 0.12), 0.3)
    mx.add(mid("c5_3", 0.45), bell(880.0, 1.2), 0.45)
    mx.add(S("c5_6") + 0.3, chord([261.6, 329.6, 392.0], 1.2), 0.35)
    # 6章
    mx.add(S("c6_4") + 0.1, blip(659.3, 0.12), 0.3)
    mx.add(S("c6_5") + 0.1, whoosh(0.6), 0.3)
    mx.add(S("c6_6") + 0.3, blip(784.0, 0.15), 0.3)
    mx.add(mid("c6_9", 0.5), bell(1046.5, 1.4), 0.45)
    mx.add(S("c6_10") + 0.1, whoosh(0.6), 0.3)
    mx.add(S("c6_11") + 0.3 * dur("c6_11"), chord([392.0, 493.9, 587.3], 1.2), 0.35)
    # まとめ・着地
    mx.add(S("c7_2") + 0.3, blip(659.3, 0.12), 0.3)
    mx.add(S("c7_3") + 0.3, bell(659.3, 1.0), 0.35)
    mx.add(S("c8_3") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S("c8_4") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻（章ごとに要所を2枚以上）
# ============================================================
def still_times():
    ts = [0.0, 0.3, S("c0_2") + 1.0, S("c0_5") + 1.5, RUN0.t0 + 1.5, RUN0.finish("walk") - 0.3, mid("c0_7b", 0.9),
          S("c0_8") + 1.2, mid("c1_1", 0.9), mid("c1_3", 0.9),
          S("ch1") + 0.8, RUN1.t0 + 2.0, RUN1.finish("walk") - 0.2, mid("c2_3", 0.9), mid("c2_4", 0.95), mid("c2_5", 0.9),
          S("g2b") + 0.8, S("g2b") + 4.0, E("g2b") - 0.3, mid("c2_7", 0.9), mid("c2_8b", 0.95),
          S("ch2") + 0.8, mid("c3_2", 0.9), mid("c3_4", 0.95), mid("c3_5", 0.9), mid("c3_7", 0.95), mid("c3_8b", 0.9),
          mid("c3_10b", 0.9),
          S("ch3") + 0.8, mid("c4_2b", 0.3), mid("c4_2b", 0.7), mid("c4_3", 0.9), mid("c4_4", 0.95), mid("c4_5", 0.95),
          mid("c4_6", 0.9), mid("c4_7", 0.9), mid("c4_8", 0.9), mid("c4_9b", 0.9),
          S("ch4") + 0.8, mid("c5_2", 0.9), mid("c5_3", 0.9), mid("c5_5", 0.9), mid("c5_7", 0.9),
          S("ch5") + 0.8, mid("c6_3", 0.8), mid("c6_4", 0.95), mid("c6_5", 0.95), mid("c6_6", 0.9), mid("c6_8b", 0.95),
          mid("c6_9", 0.95), mid("c6_10", 0.95), mid("c6_10b", 0.9), mid("c6_11", 0.9),
          mid("c0_1", 0.9), mid("c0_6", 0.9), mid("c3_9b", 0.9), mid("c7_4", 0.9), mid("c7_5c", 0.9),
          S("ch6") + 0.8, mid("c7_3", 0.9), mid("c7_5b", 0.9), mid("c7_7b", 0.9), mid("c7_9", 0.9), mid("c8_2", 0.9),
          S("c8_3") + 1.5, S("c8_4") + 1.5, DUR - 0.1]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


# ============================================================
# 文字起こし（合戦ロングと同じ形）と、画面の文字がどれだけの間見えているか
# ============================================================
def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・映像だけ）")
        else:
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def text_spans(step=0.25, scale=0.25):
    """画面の文字（字幕を除く）が見えている区間。core.text のログを使う"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    seen = {}
    n = int(DUR / step)
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        for e in core._LOG:
            seen.setdefault(e[1], []).append(t)
        core._LOG = None
    spans = []
    for s_, ts in seen.items():
        a = b = ts[0]
        for x in ts[1:] + [1e9]:
            if x - b > step * 1.5:
                spans.append((a, b + step, s_))
                a = x
            b = x
    spans.sort()
    return spans


def write_screen_text(path, spans):
    rows = ["# 画面の文字（字幕を除く）と、見えている区間。0.25秒ごとに描いて調べた", ""]
    for a, b, s_ in spans:
        mark = "  ←短い" if b - a < 1.5 and not any(ch.isdigit() for ch in s_) else ""
        rows.append(f"{_ts(a)}〜{_ts(b)}（{b - a:4.1f}秒） {s_}{mark}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("画面の文字:", path)


def update_description():
    """publish/ame-long/description.txt の「▼チャプター」の段を、書き出した chapters.txt の時刻に差し替える"""
    f = Path(__file__).resolve().parents[1] / "publish" / SLUG / "description.txt"
    if not f.exists():
        return
    lines = f.read_text(encoding="utf-8").split("\n")
    i = lines.index("▼チャプター")
    j = i + 1
    while j < len(lines) and lines[j].strip():
        j += 1
    lines[i + 1:j] = tl.chapter_text().split("\n")
    f.write_text("\n".join(lines), encoding="utf-8")
    print("概要欄のチャプターを差し替え:", f)


# ============================================================
# 場面の照合（画面に出す数字・読み上げる数字が data.json と合っているか・見本の点・長さ）
# ============================================================
def scene_checks():
    c1, c2, c4, c5, c6 = RES["ch1"], RES["ch2"], RES["ch4"], RES["ch5"], RES["ch6"]
    r3 = {f"{r['v']}": r for r in RES["ch3"]["rows"]}
    hu = {r["Hu"]: r for r in c4["hu_sweep"]}
    h5 = c5["head"]["rows"][1]
    um = c4["umbrellas"]
    z0, z1 = c5["tail"]["zero_flat"][0]
    tr5 = {r["v"]: r for r in c5["tail"]["rows"]}
    hr5 = {r["v"]: r for r in c5["head"]["rows"]}
    checks = [
        ("0章「秒速6.5m」＝ 雨粒の落ちる速さ 6.49m/s の丸め", round(U, 1), 6.5, 0),
        ("0章「秒速1.4m、時速5km」", round(V_WALK * 3.6), 5, 0),
        ("0章「秒速5m、時速18km」", round(V_RUN * 3.6), 18, 0),
        ("0章「約13,100粒」（傘なし・歩き）", r100(c1["walk_plain"]), 13100, 0),
        ("0章「約9,300粒」（傘なし・走り）", r100(c1["run_plain"]), 9300, 0),
        ("0章「約3割減」", CUT_TENTHS, 3, 0),
        ("1章「直径1m」", DU, 1.0, 0),
        ("1章「高さ1.9m」", HU, 1.9, 0),
        ("2章「約1,100粒」（傘あり・歩き）", r100(c1["walk_umb"]), 1100, 0),
        ("2章「約6,600粒」（傘あり・走り）", r100(c1["run_umb"]), 6600, 0),
        ("2章「約6倍」", UMB_TIMES, 6, 0),
        ("2章「1割ちょっと」（傘あり歩き÷傘なし走り が 1割〜1割5分）", float(0.10 <= c6["walk_umb_vs_plain_run"] < 0.15), 1, 0),
        ("2章「時速3.6km」（1万人の一番ゆっくり）", round(V_LO * 3.6, 1), 3.6, 0),
        ("2章「25km」（1万人の一番速い）", round(V_HI * 3.6), 25, 0),
        ("2章「時速4km以下なら、ほぼ0粒」（1粒未満になる最大の速さ）", round(c1["zero"][0][1] * 3.6), 4, 0),
        ("2章 散布図: data.npz の1万人", len(VS_ALL), N_PEOPLE, 0),
        ("2章 散布図: 速さの範囲 1〜7m/s", float(VS_ALL.min() >= V_LO and VS_ALL.max() <= V_HI), 1, 0),
        ("2章 散布図: 傘なしの1万人の平均は (a) と矛盾しない（data.json の people）", float(H_PLAIN.mean()), RES["people"]["plain_calm"]["mean"], 0.5),
        ("2章 散布図: 傘ありは速いほど増える（曲線 (a) が単調増加）", float(all(b["umb"] >= a["umb"] - 1e-9 for a, b in zip(c1["curve"], c1["curve"][1:]))), 1, 0),
        ("2章 散布図: 傘なしは速いほど減る（曲線 (a) が単調減少）", float(all(b["plain"] <= a["plain"] + 1e-9 for a, b in zip(c1["curve"], c1["curve"][1:]))), 1, 0),
        ("3章「約12度」", round(apparent_angle(V_WALK)), 12, 0),
        ("3章「約38度」", round(apparent_angle(V_RUN)), 38, 0),
        ("3章「濡れるのは、地面から40cmまで」（歩き・体の端。中心線はそれより低い）", round(c2["1.4"]["umb"]["z_dry_edge"] * 10) * 10, 40, 0),
        ("3章「速く進むと浴びる時間が短くなって、ちょうど打ち消し合う」（傘なしの前から 歩き＝走り）",
         c2["1.4"]["plain"]["face"], c2["5.0"]["plain"]["face"], 1e-6),
        ("3章「約140cm」（走り・中心線 141cm の丸め）", round(c2["5.0"]["umb"]["z_dry_center"] * 10) * 10, 140, 0),
        ("3章「頭と肩だけ乾く」（走りの濡れる高さ < 体の高さ 1.7m − 頭）", float(c2["5.0"]["umb"]["z_dry_edge"] < 1.5), 1, 0),
        ("3章「約7,800粒」（傘なしで前から）", r100(c1["floor"]), 7800, 0),
        ("3章 傘の影の絵: 中心線の濡れる高さを左ページの影の多角形で出すと、モデルと同じ（走り、m）",
         float(_shadow_dry(V_RUN, 0.0)), c2["5.0"]["umb"]["z_dry_center"], 0.01),
        ("3章 傘の影の絵: 同じく歩き（m）", float(_shadow_dry(V_WALK, 0.0)), c2["1.4"]["umb"]["z_dry_center"], 0.01),
        ("4章（改）「腕の届く範囲（肩から60cm）」", ARM, 0.6, 0),
        ("4章（改）「一番効く傾きは、雨の傾きと、ぴったり同じ」（歩き・走りとも 傾き＝雨の見かけの角度）",
         (ARM_CALM["walk"]["phi"], ARM_CALM["run"]["phi"]), (apparent_angle(V_WALK), apparent_angle(V_RUN)), 0.05),
        ("4章（改）「12度」「38度」", (round(ARM_CALM["walk"]["phi"]), round(ARM_CALM["run"]["phi"])), (12, 38), 0),
        ("4章（改）「歩く人は…0粒」", ARM_CALM["walk"]["e"], 0.0, 0.5),
        ("4章（改）「傘を少し前へ」（歩き: 前へ 0〜30cm）", float(0.0 < ARM_CALM["walk"]["cx"] <= 0.3), 1, 0),
        ("4章（改）「体の70cm前まで突き出す」（走り: 傘の中心 前へ）", round(ARM_CALM["run"]["cx"] * 100), 70, 0),
        ("4章（改）「約6,600粒が、約2,000粒」", (r100(c1["run_umb"]), r100(ARM_CALM["run"]["e"])), (6600, 2000), 0),
        ("4章（改）「3分の1以下」", float(ARM_CALM["run"]["e"] < c1["run_umb"] / 3), 1, 0),
        ("4章（改）「地面から30cmくらいまで」（前の濡れる高さ 中心線〜端の中ほど、10cm単位）",
         round((ARM_CALM["run"]["z_dry_center"] + ARM_CALM["run"]["z_dry_edge"]) / 2 * 10) * 10, 30, 0),
        ("4章（改）「直径1m30cmより大きい傘が要る」（体の影を覆う最小の直径が 1.30〜1.40m）",
         float(1.30 < d_need(apparent_angle(V_RUN)) <= 1.40), 1, 0),
        ("4章（改）「縦に長い体は、直径1mの傘の円に収まりきらない」（必要な直径 > 1m）", float(d_need(apparent_angle(V_RUN)) > DU), 1, 0),
        ("4章（改）「前に出して傾けても、歩くほうが濡れない」", float(ARM_CALM["walk"]["e"] < ARM_CALM["run"]["e"]), 1, 0),
        ("4章（改）傘の影の絵: 前に出して傾けた走りの濡れる高さ（中心線、m）",
         float(_shadow_dry(V_RUN, ARM_CALM["run"]["phi"], ARM_CALM["run"]["cx"], ARM_CALM["run"]["hu"])), ARM_CALM["run"]["z_dry_center"], 0.012),
        ("5章「約2,200粒」（折りたたみ・歩き）", r100(um["折りたたみ傘"]["walk"]["flat"]), 2200, 0),
        ("5章「約6,900粒」（折りたたみ・走り）", r100(um["折りたたみ傘"]["run"]["flat"]), 6900, 0),
        ("5章「0粒」（大きな傘・歩き）", r100(um["ゴルフ傘"]["walk"]["flat"]), 0, 0),
        ("5章「約6,000粒」（大きな傘・走り）", r100(um["ゴルフ傘"]["run"]["flat"]), 6000, 0),
        ("5章 直径「90cm」「1m20cm」", (um["折りたたみ傘"]["Du"], um["ゴルフ傘"]["Du"]), (0.9, 1.2), 0),
        ("5章 走りの列「6,900 → 6,600 → 6,000」", (r100(um["折りたたみ傘"]["run"]["flat"]), r100(um["長傘"]["run"]["flat"]),
                                                  r100(um["ゴルフ傘"]["run"]["flat"])), (6900, 6600, 6000), 0),
        ("5章「差が広がる」（走り−歩き が 直径とともに増える）",
         float((um["ゴルフ傘"]["run"]["flat"] - um["ゴルフ傘"]["walk"]["flat"]) > (um["長傘"]["run"]["flat"] - um["長傘"]["walk"]["flat"])
               > (um["折りたたみ傘"]["run"]["flat"] - um["折りたたみ傘"]["walk"]["flat"])), 1, 0),
        ("6章「秒速3m」", WIND, 3.0, 0),
        ("6章「追い風だと、歩くと約2,400粒、走ると約1,400粒」（まっすぐ）", (r100(tr5[V_WALK]["flat"]), r100(tr5[V_RUN]["flat"])), (2400, 1400), 0),
        ("6章「向かい風だと、歩くと約19,800粒、走ると約11,800粒」（まっすぐ）", (r100(hr5[V_WALK]["flat"]), r100(hr5[V_RUN]["flat"])), (19800, 11800), 0),
        ("6章「風が吹くと、まっすぐ持った傘では、走ったほうが濡れない」",
         float(tr5[V_RUN]["flat"] < tr5[V_WALK]["flat"] and hr5[V_RUN]["flat"] < hr5[V_WALK]["flat"]), 1, 0),
        ("6章「追い風では、雨が、歩く人には後ろから、走る人には前から」（c = w − v の符号）", float(WIND - V_WALK > 0 and WIND - V_RUN < 0), 1, 0),
        ("6章「歩く人は後ろへ、走る人は前へ傾ける」", float(ARM_TAIL["walk"]["phi"] < 0 < ARM_TAIL["run"]["phi"]), 1, 0),
        ("6章 画面「後ろへ14°・前へ17°」", (round(-ARM_TAIL["walk"]["phi"]), round(ARM_TAIL["run"]["phi"])), (14, 17), 0),
        ("6章「歩いても、走っても、0粒」（追い風・雨に向ける (ii')）", (ARM_TAIL["walk"]["e"], ARM_TAIL["run"]["e"]), (0.0, 0.0), 0.5),
        ("6章「向かい風では、歩いても約5,000粒、走っても約4,900粒」", (r100(ARM_HEAD["walk"]["e"]), r100(ARM_HEAD["run"]["e"])), (5000, 4900), 0),
        ("6章「ほとんど同じ」（差が5%未満）", float(abs(ARM_HEAD["walk"]["e"] - ARM_HEAD["run"]["e"]) / ARM_HEAD["walk"]["e"] < 0.05), 1, 0),
        ("6章「傘を前に出しても、0にはならない」（向かい風）", float(min(ARM_HEAD["walk"]["e"], ARM_HEAD["run"]["e"]) > 100), 1, 0),
        ("6章「風の日は、速さより、傘を雨に向けるほうが効く」（向ける効果 ＞ 速さの差。追い風・向かい風とも）",
         float(min(tr5[V_WALK]["flat"], tr5[V_RUN]["flat"]) - max(ARM_TAIL["walk"]["e"], ARM_TAIL["run"]["e"])
               > abs(ARM_TAIL["walk"]["e"] - ARM_TAIL["run"]["e"])
               and min(hr5[V_WALK]["flat"], hr5[V_RUN]["flat"]) - max(ARM_HEAD["walk"]["e"], ARM_HEAD["run"]["e"])
               > abs(ARM_HEAD["walk"]["e"] - ARM_HEAD["run"]["e"])), 1, 0),
        ("7章「傘を雨に向けて前に出せば、歩けば0粒。走っても約2,000粒」", (r100(ARM_CALM["walk"]["e"]), r100(ARM_CALM["run"]["e"])), (0, 2000), 0),
        ("7章「まっすぐ持つと、走るほうが約6倍」", UMB_TIMES, 6, 0),
        ("7章「持つ高さ ±10cm → 歩き 約700〜1,600粒」", (r100(hu[1.8]["walk"]["flat"]), r100(hu[2.0]["walk"]["flat"])), (700, 1600), 0),
        ("7章「倍以上変わる」", float(hu[2.0]["walk"]["flat"] / hu[1.8]["walk"]["flat"] >= 2.0), 1, 0),
        ("7章「どの傘でも 傘ありならゆっくり」（無風・まっすぐで 走り > 歩き、3種類とも）",
         float(all(e["run"]["flat"] > e["walk"]["flat"] for e in um.values())), 1, 0),
        ("7章「どの持ち方でも」（無風・前に出して傾けても 走り > 歩き、3種類とも）",
         float(all(r_["rows"][[x["v"] for x in r_["rows"]].index(V_RUN)]["ii"]["e"] > r_["rows"][[x["v"] for x in r_["rows"]].index(V_WALK)]["ii"]["e"]
                   for r_ in CB["umbrellas"].values() if r_["Du"] <= 1.2 + 1e-9)), 1, 0),
        ("1万人の小さな人: 濡れる高さの式がモデル（走り 141cm）と同じ", z_dry_flat(V_RUN), c2["5.0"]["umb"]["z_dry_center"], 0.006),
        ("1万人の小さな人: 一番ゆっくり（約1m/s）は濡れない", z_dry_flat(min(CROWD_V)), 0.0, 0),
    ]
    for name, (v, w, du, phi, hu_, cx_) in SAMPLE_DEFS.items():
        sd = SEEDS[name]
        e = expected(v, w, du, hu_, phi, cx=cx_)
        lay = layer(name)
        checks.append((f"絵 見本 {name}: 体の点の数 ＝ 雨粒をまいた結果（person_mc と同じ）", float(len(lay.t)), float(sd["n"]), 0))
        checks.append((f"絵 見本 {name}: ふつうの結果（期待値 {e:,.0f} との差が √期待値 の2倍＋1 以内）", float(sd["n"]), e, 2 * math.sqrt(e) + 1))
    checks += [
        ("絵 0章の早回し: 歩く人は「歩くと…」の前に 100m に着く", float(RUN0.finish("walk") < S("c0_7")), 1, 0),
        ("絵 2章の早回し: 歩く人は「歩いた人は…」の前に 100m に着く", float(RUN1.finish("walk") < S("c2_2")), 1, 0),
        ("絵 1万人の点は無音の区間のうちに全部出る", float(T_D1() <= E("g2b")), 1, 0),
        ("絵 1万人の小さな人は章の終わりまでに全員出る", float(T_C0() + 0.27 * (CROWD_N - 1) + 0.9 < S("ch2")), 1, 0),
        ("絵 4章・6章・7章: 描いた傘（円板）が体（10cm太らせた箱）にめり込まない（0.1秒ごと）", float(_disc_clear()), 1, 0),
        ("絵 4章: 描いた傘の置き方＝モデル（走り: 傾き・中心の前・高さ）",
         (*umb_state("run", S("c4_6") + 0.5),), (ARM_CALM["run"]["phi"], ARM_CALM["run"]["cx"], ARM_CALM["run"]["hu"]), 1e-6),
        ("絵 4章: 描いた傘の置き方＝モデル（歩き）",
         (*umb_state("walk", S("c4_5")),), (ARM_CALM["walk"]["phi"], ARM_CALM["walk"]["cx"], ARM_CALM["walk"]["hu"]), 1e-6),
        ("絵 6章: 追い風で雨に向けた置き方＝モデル (ii')（歩き・走り）",
         (*umb_state("walk", S("c6_9") + 0.5), *umb_state("run", S("c6_9") + 0.5)),
         (ARM_TAIL["walk"]["phi"], ARM_TAIL["walk"]["cx"], ARM_TAIL["walk"]["hu"], ARM_TAIL["run"]["phi"], ARM_TAIL["run"]["cx"], ARM_TAIL["run"]["hu"]), 1e-6),
        ("絵 6章: 向かい風で雨に向けた置き方＝モデル（歩き・走り）",
         (*umb_state("walk", mid("c6_10", 0.8)), *umb_state("run", mid("c6_10", 0.8))),
         (ARM_HEAD["walk"]["phi"], ARM_HEAD["walk"]["cx"], ARM_HEAD["walk"]["hu"], ARM_HEAD["run"]["phi"], ARM_HEAD["run"]["cx"], ARM_HEAD["run"]["hu"]), 1e-6),
        ("絵: 4章・6章で手が肩から腕の長さ以内（モデルの in_reach。追い風の歩きは体の後ろも可）", float(_hands_ok()), 1, 0),
        ("長さ 8分00秒〜9分00秒（一呼吸を入れて9分弱まで）", DUR, 510, 30),
    ]
    flat = []
    for name, v, e, tol in checks:                      # 組の値は1つずつに分ける（check_answers は数1つずつ）
        if isinstance(v, tuple):
            flat += [(f"{name}（{i + 1}つ目）", float(vi), float(ei), tol) for i, (vi, ei) in enumerate(zip(v, e))]
        else:
            flat.append((name, float(v), float(e), tol))
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


def _shadow_dry(v, phi, ux=0.0, hu=HU):
    """左ページの傘の影の多角形（画面 px）から、体の前の面（x=+BL/2）の濡れる高さ（m）を出す（絵の照合用）"""
    slant = -v / U
    poly = shadow_poly(0.0, GY, DU, phi, slant, ux=ux, hu=hu)
    xf = BL / 2 * K
    # 前の縁から地面までの線（雨の向き）が x=xf を横切る高さ（その下は影の外＝濡れる）
    (x1, y1), (x2, y2) = poly[1], poly[2]
    if abs(x2 - x1) < 1e-9:
        return 0.0
    u = (xf - x1) / (x2 - x1)
    y = y1 + (y2 - y1) * u
    return max(0.0, min(BH, (GY - y) / K))


def _disc_clear(step=0.1):
    """傘を動かす区間（4章・6章・7章）で、描いた円板が体の箱（10cm太らせたもの）にめり込まないか"""
    for a_, b_ in ((S("ch3"), S("ch4") + 1.0), (S("ch5"), S("ch6") + 1.0), (S("c7_4"), S("c7_5") + 1.0)):
        for t in np.arange(a_, b_, step):
            for c in COLS:
                ph, ux, hu = umb_state(c, t)
                if disc_hits_body(ux, hu, ph, DU):
                    print(f"  めり込み: {c} t={t:.1f} φ={ph:.1f} 中心=({ux:.2f},{hu:.2f})")
                    return False
    return True


def _hands_ok(step=0.1):
    for a_, b_ in ((S("ch3"), S("ch4") + 1.0), (S("ch5"), S("ch6") + 1.0), (S("c7_4"), S("c7_5") + 1.0)):
        for t in np.arange(a_, b_, step):
            for c in COLS:
                ph, ux, hu = umb_state(c, t)
                hx, hz = hand_from_center(ux, hu, ph)
                if not in_reach(hx, hz, ARM + 0.01, behind=True):
                    print(f"  届かない: {c} t={t:.1f} 手=({hx:.2f},{hz:.2f})")
                    return False
    return True


# ============================================================
# 書き出し
#   python -X utf8 sims/ame-long.py --check        数字の照合だけ（モデル 192件）
#   python -X utf8 sims/ame-long.py --readings     合成エンジンが読むカナ（数字の読み違いの確認）
#   python -X utf8 sims/ame-long.py --stills       要所の静止画と sheet.png（out/ame-long/stills/）。--at 12.3,40.5 なら指定した秒だけ
#   python -X utf8 sims/ame-long.py --textcheck    画面の文字が見えている区間（out/ame-long/screen_text.txt）
#   python -X utf8 sims/ame-long.py --scenecheck   場面の照合だけ（画面の数字・見本の点・長さ）
#   python -X utf8 sims/ame-long.py --preview      960×540・15fps の確認用
#   python -X utf8 sims/ame-long.py                照合 → 本番（mp4・chapters.txt・transcript.long.txt・screen_text.txt）
#   --fake-voice をつけると、AivisSpeech なしで長さを見積もる（無音。静止画の確認用。本番では使えない）
# ============================================================
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for i, (t0_, title) in enumerate(tl.chapters):
        print(f"  {lf._mmss(t0_)} {title}")
    if "--readings" in sys.argv:
        from engine import voice
        for it in tl.items:
            if isinstance(it, lf.Line):
                shown, spoken = split_reading(it.text)
                print(f"{it.id}: {shown}\n    → {voice.read_aloud(spoken)}")
        raise SystemExit
    if "--wraps" in sys.argv:                          # 字幕の折り返しを全部表示（語の途中で折れていないか）
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        raise SystemExit
    if "--scenecheck" in sys.argv:
        scene_checks()
        raise SystemExit
    if "--textcheck" in sys.argv:
        write_screen_text(OUT / "screen_text.txt", text_spans())
        raise SystemExit
    if "--stills" in sys.argv:
        if "--at" in sys.argv:
            ts = [float(x) for x in sys.argv[sys.argv.index("--at") + 1].split(",")]
            for tt in ts:
                lf.still(draw, tt, OUT / f"at_{tt:06.1f}.png")
        else:
            lf.stills(draw, still_times(), OUT / "stills")
    elif "--preview" in sys.argv:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
    else:
        if FAKE:
            raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
        check(RES)
        scene_checks()
        lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
        write_transcript(OUT / "transcript.long.txt")
        update_description()
        write_screen_text(OUT / "screen_text.txt", text_spans())
        print("完成:", OUT / f"{SLUG}.mp4")
