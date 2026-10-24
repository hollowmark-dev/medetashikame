"""歩いて測った日本地図は、どこまで正確になる？【1万回シミュレーション】（横型ロング・チャンネル「めでたしかめ」）

このファイルは公開日まで非公開（答えが書いてある）。
前半はモデル（数字の計算・照合・数字の書き出し・伊能図の位置合わせ）。後半（「# ここから下は場面」から）が場面（描画・音・照合・書き出し。okehazama-long.py と同じ並び）。
モデルの計算は下絵 sims/inoh-long.draft.py と同じ（同じ種・同じ順番で乱数を引く＝結果は out/inoh-long/proto/tables.md と一致する）。

■ モデル（下絵のとおり。値はすべて【仮定】または資料の値。動画で「〜と置きます」と言う）
  道すじ   : 第1次測量（1800年・江戸→奥州街道→蝦夷地の南東岸→西別）を、実在の地点の緯度経度を結んだ折れ線で近似（約1,376km・1,377区間）
  1回の測量: 道すじを約1kmの区間に分け、区間ごとに「距離」と「方位」を測り、前の点から足して地図を描く
             距離のぶれ = 1回ごとの偏り（その回の全区間に同じ倍率）× 区間ごとのぶれ ／ 方位のぶれ = 区間ごとのぶれ + 1回ごとの偏り
  星       : 一定の距離ごとに緯度（南北の位置）を星で測り、描いた地図の南北の位置を測った値に描き直す（観測のぶれあり）。東西は直せない
  ずれ     : 描いた地図の各点と本当の点の距離の平均（km）。1万回を小さい順に並べた真ん中（中央値）
  段       : 0 目分量 → 1 歩幅をそろえる → 2 ＋磁石で方位 → 3 ＋星で緯度 → 4 ＋縄・鎖で距離（累積）
  第7章    : 江戸から約600km北へ測った距離 ÷ 星で測った緯度の差 ＝「緯度1度の長さ」。地球は半径6371kmの球（1度＝111.19km）
  海岸線   : 地球地図日本（国土地理院）第2.2版 coastl_jpn（data/gsi_globalmap/）を自前で読んで描く
  伊能図   : 東京国立博物館「日本沿海輿地図（中図）」北海道東部 P-2906-1・九州南部 P-2906-8（ColBase・data/colbase_ino/）。
             図の経緯線（緯線＝水平「北四十三度」など、経線＝斜め「東十度」など。京都を通る経線＝中度からの度数）から画像の位置を緯度経度に直し、
             今の地図の岬などの座標と比べて、「やや東にずれている」矢印の向きと長さを決める。京都の経度は 135.77°E と置く（--ino で測った値は ino_offsets.md）

使い方
  python -X utf8 sims/inoh-long.py --numbers   計算 → 照合 → out/inoh-long/data.json・numbers.md・ino_reg.json・ino_offsets.md・credits.txt（1〜2分）
  python -X utf8 sims/inoh-long.py --check     data.json を読んで照合だけ
  python -X utf8 sims/inoh-long.py --ino       伊能図の位置合わせだけやり直す（ino_reg.json・ino_offsets.md）
  python -X utf8 sims/inoh-long.py --scenecheck --fake-voice   場面の照合（音声なし）
  python -X utf8 sims/inoh-long.py --stills --fake-voice       要所の静止画と sheet_480.png・ch6_compare_480.png（詳しくは場面の部分の先頭）
"""
import json
import math
import re
import struct
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLUG = "inoh-long"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "out" / SLUG
COAST_SHP = ROOT / "data" / "gsi_globalmap" / "gm-jpn-all_u_2_2" / "coastl_jpn.shp"
INO_DIR = ROOT / "data" / "colbase_ino"
INO_FILES = {"hokkaido": INO_DIR / "P-2906-1" / "P-2906-1_C0020839.jpg", "kyushu": INO_DIR / "P-2906-8" / "P-2906-8_C0020862.jpg"}

# ============================================================
# 0. 道すじ・条件（下絵と同じ）
# ============================================================
ROUTE = [
    ("江戸", 35.69, 139.77), ("宇都宮", 36.56, 139.88), ("白河", 37.13, 140.21), ("郡山", 37.40, 140.38),
    ("仙台", 38.27, 140.87), ("一関", 38.93, 141.13), ("盛岡", 39.70, 141.15), ("三戸", 40.38, 141.26),
    ("青森", 40.82, 140.74), ("三厩", 41.21, 140.42), ("函館", 41.77, 140.73), ("森", 42.11, 140.57),
    ("長万部", 42.51, 140.38), ("伊達", 42.47, 140.87), ("室蘭", 42.32, 140.97), ("白老", 42.55, 141.36),
    ("苫小牧", 42.63, 141.60), ("静内", 42.33, 142.37), ("浦河", 42.17, 142.77), ("様似", 42.13, 142.93),
    ("襟裳", 41.93, 143.25), ("広尾", 42.29, 143.32), ("大津", 42.68, 143.65), ("白糠", 42.95, 144.07),
    ("釧路", 42.98, 144.38), ("厚岸", 43.05, 144.85), ("浜中", 43.08, 145.12), ("西別", 43.39, 145.12),
]
R_EARTH = 6371.0
SEG_KM = 1.0
N = 10000
SEED = 20261022
SEED_PAIR = 99
KYOTO_LON = 135.77


def to_xy(lat, lon, lat0=38.5, lon0=141.5):
    """km（東西 x・南北 y）。小さな範囲の正距円筒"""
    x = math.radians(lon - lon0) * R_EARTH * math.cos(math.radians(lat0))
    y = math.radians(lat - lat0) * R_EARTH
    return x, y


def dense_path():
    pts = np.array([to_xy(la, lo) for _, la, lo in ROUTE])
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        d = np.hypot(*(b - a))
        k = max(1, int(round(d / SEG_KM)))
        for i in range(1, k + 1):
            out.append(a + (b - a) * i / k)
    return np.array(out)


TRUE = dense_path()
LEG = np.diff(TRUE, axis=0)
DIST = np.hypot(LEG[:, 0], LEG[:, 1])
BEAR = np.arctan2(LEG[:, 0], LEG[:, 1])          # 北から時計回り（rad）
CUM = np.concatenate([[0], np.cumsum(DIST)])

# 段（条件）。値はすべて仮定（下絵と同じ）
LADDER = [
    dict(name="0 目分量で歩いて描く", d_bias=0.10, d_rand=0.15, b_bias=3.0, b_rand=8.0, star=None),
    dict(name="1 歩幅をそろえて歩測", d_bias=0.02, d_rand=0.05, b_bias=3.0, b_rand=8.0, star=None),
    dict(name="2 ＋磁石で方位を測る", d_bias=0.02, d_rand=0.05, b_bias=0.3, b_rand=0.3, star=None),
    dict(name="3 ＋星で緯度を直す", d_bias=0.02, d_rand=0.05, b_bias=0.3, b_rand=0.3, star=dict(every_km=30.0, err_km=0.9)),
    dict(name="4 ＋縄・鎖で距離を測る", d_bias=0.003, d_rand=0.01, b_bias=0.3, b_rand=0.3, star=dict(every_km=30.0, err_km=0.9)),
]
STEP_KEYS = ["L0", "L1", "L2", "L3", "L4"]
STAR_EVERY = (10.0, 30.0, 100.0, 300.0)


def survey(rng, c, n):
    """n 回ぶんの地図（n × 点 × 2）"""
    m = len(DIST)
    d = DIST * (1 + rng.normal(0, c["d_bias"], (n, 1))) * (1 + rng.normal(0, c["d_rand"], (n, m)))
    b = BEAR + np.radians(rng.normal(0, c["b_bias"], (n, 1)) + rng.normal(0, c["b_rand"], (n, m)))
    dx, dy = d * np.sin(b), d * np.cos(b)
    if c["star"] is None:
        x = np.concatenate([np.zeros((n, 1)), np.cumsum(dx, 1)], 1) + TRUE[0, 0]
        y = np.concatenate([np.zeros((n, 1)), np.cumsum(dy, 1)], 1) + TRUE[0, 1]
        return np.stack([x, y], -1)
    # 星で緯度を直す: 一定距離ごとに y を（観測誤差つきの）本当の値に置き直す。x は直さない
    every, err = c["star"]["every_km"], c["star"]["err_km"]
    fix_at = set(np.searchsorted(CUM, np.arange(every, CUM[-1], every)))
    x = np.empty((n, m + 1))
    y = np.empty((n, m + 1))
    x[:, 0], y[:, 0] = TRUE[0]
    for i in range(m):
        x[:, i + 1] = x[:, i] + dx[:, i]
        y[:, i + 1] = y[:, i] + dy[:, i]
        if i + 1 in fix_at:
            y[:, i + 1] = TRUE[i + 1, 1] + rng.normal(0, err, n)
    return np.stack([x, y], -1)


def survey_pair(rng, c, n):
    """画面用（第4章）: 同じ歩き（同じ乱数）で、星で直す前と後を並べて返す。主な数字には使わない（別の乱数）。x は同じ・y だけ変わる"""
    m = len(DIST)
    d = DIST * (1 + rng.normal(0, c["d_bias"], (n, 1))) * (1 + rng.normal(0, c["d_rand"], (n, m)))
    b = BEAR + np.radians(rng.normal(0, c["b_bias"], (n, 1)) + rng.normal(0, c["b_rand"], (n, m)))
    dx, dy = d * np.sin(b), d * np.cos(b)
    x0 = np.concatenate([np.zeros((n, 1)), np.cumsum(dx, 1)], 1) + TRUE[0, 0]
    y0 = np.concatenate([np.zeros((n, 1)), np.cumsum(dy, 1)], 1) + TRUE[0, 1]
    every, err = c["star"]["every_km"], c["star"]["err_km"]
    fix_at = set(np.searchsorted(CUM, np.arange(every, CUM[-1], every)))
    y1 = np.empty((n, m + 1))
    y1[:, 0] = TRUE[0, 1]
    for i in range(m):
        y1[:, i + 1] = y1[:, i] + dy[:, i]
        if i + 1 in fix_at:
            y1[:, i + 1] = TRUE[i + 1, 1] + rng.normal(0, err, n)
    return np.stack([x0, y0], -1), np.stack([x0, y1], -1)


def stats(maps):
    e = np.hypot(*(maps - TRUE[None]).transpose(2, 0, 1))
    return e.mean(1), e[:, -1]


def degree_length(rng, c, n, lat_err_km=0.9):
    """第7章: 江戸から北へ測った南北の距離 ÷ 星で測った緯度の差 ＝「緯度1度の長さ」（本当の1度は R×π/180）"""
    m = len(DIST)
    d = DIST * (1 + rng.normal(0, c["d_bias"], (n, 1))) * (1 + rng.normal(0, c["d_rand"], (n, m)))
    b = BEAR + np.radians(rng.normal(0, c["b_bias"], (n, 1)) + rng.normal(0, c["b_rand"], (n, m)))
    end = int(np.searchsorted(CUM, 600.0))
    ns = (d[:, :end] * np.cos(b[:, :end])).sum(1)
    true_ns = TRUE[end, 1] - TRUE[0, 1]
    true_deg = R_EARTH * math.pi / 180
    lat_meas = (true_ns + rng.normal(0, lat_err_km, n) - rng.normal(0, lat_err_km, n)) / true_deg
    return ns / lat_meas, true_deg


# ============================================================
# 1. 海岸線（地球地図日本・自前で読む）
# ============================================================
_RECS = []


def _coast_records():
    """coastl_jpn.shp の全レコード（ポリラインを500点ずつに切ったもの）を (bbox, [lon,lat] の配列) で返す"""
    if _RECS:
        return _RECS
    b = COAST_SHP.read_bytes()
    i = 100
    while i + 8 <= len(b):
        _, cl = struct.unpack(">2i", b[i:i + 8])
        rec = b[i + 8:i + 8 + cl * 2]
        i += 8 + cl * 2
        if len(rec) < 44 or struct.unpack("<i", rec[:4])[0] != 3:
            continue
        x0, y0, x1, y1 = struct.unpack("<4d", rec[4:36])
        nparts, npts = struct.unpack("<2i", rec[36:44])
        parts = struct.unpack("<%di" % nparts, rec[44:44 + 4 * nparts])
        xy = np.array(struct.unpack("<%dd" % (2 * npts), rec[44 + 4 * nparts:44 + 4 * nparts + 16 * npts])).reshape(-1, 2)
        for k in range(nparts):
            a = parts[k]
            e = parts[k + 1] if k + 1 < nparts else npts
            _RECS.append(((x0, y0, x1, y1), xy[a:e]))
    return _RECS


def read_coast_ll(lat_min, lat_max, lon_min, lon_max):
    """範囲にかかる線（[lon, lat] の配列）"""
    out = []
    for (x0, y0, x1, y1), xy in _coast_records():
        if x1 < lon_min or x0 > lon_max or y1 < lat_min or y0 > lat_max:
            continue
        out.append(xy)
    return out


def thin(xy, min_step):
    """点を間引く（隣の点から min_step 以上離れた点だけ残す。単位は xy と同じ）"""
    if len(xy) < 3:
        return xy
    keep = [0]
    last = xy[0]
    for j in range(1, len(xy) - 1):
        if math.hypot(*(xy[j] - last)) >= min_step:
            keep.append(j)
            last = xy[j]
    keep.append(len(xy) - 1)
    return xy[keep]


def read_coast(lat_min=34.5, lat_max=44.5, lon_min=138.0, lon_max=146.5):
    """下絵と同じ範囲の海岸線を km 座標（to_xy）で。0.8km より細かい点は間引く"""
    out = []
    for xy in read_coast_ll(lat_min, lat_max, lon_min, lon_max):
        k = np.array([to_xy(la, lo) for lo, la in xy])
        out.append(thin(k, 0.8))
    return out


# ============================================================
# 2. 伊能図の位置合わせ（経緯線 → 緯度経度）
# ============================================================
# 目で読んだ経緯線の位置（図の左上を原点とした画像の画素。--ino がこの近くの線を追いかけて直線にあてはめる）
#   hl: 緯線（水平）の「北緯 → y」／ vl: 経線（斜め）の「京都からの度数 → (y=0 での x, 傾き)」。東＝＋・西＝−
INO_GRID = {
    "hokkaido": dict(hl={45: 248, 44: 1019, 43: 1793, 42: 2567},
                     vl={8: (66, .0875), 9: (600, .1025), 10: (1150, .11), 11: (1696, .12), 12: (2232, .1375)}),
    "kyushu": dict(hl={32: 658, 31: 1490, 30: 2331},
                   vl={-7: (124, -.0725), -6: (826, -.065), -5: (1526, -.055), -4: (2232, -.045)}),
}
# 画像の上で目で拾った地点（画素）と、今の地図の側の探し方（範囲内の最も北／南／東／西の点）
#   名前, 画素(x, y)（原寸2477×3000・2691×3000）, 今の地図で探す範囲 (lat0, lat1, lon0, lon1), 何を取るか
INO_POINTS = {
    "hokkaido": [
        ("納沙布岬", (1797, 1520), (43.2, 43.5, 145.5, 145.9), "east"),
        ("襟裳岬", (320, 2648), (41.8, 42.1, 143.0, 143.5), "south"),
        ("知床岬", (1505, 900), (44.0, 44.5, 144.9, 145.45), "north"),
    ],
    "kyushu": [
        ("佐多岬", (1476, 1498), (30.9, 31.2, 130.5, 130.9), "south"),
        ("屋久島の西はし", (1267, 2008), (30.2, 30.55, 130.35, 130.7), "west"),
        ("屋久島の東はし", (1475, 2008), (30.2, 30.55, 130.35, 130.7), "east"),
        ("種子島の北はし", (1757, 1633), (30.3, 30.9, 130.8, 131.1), "north"),
        ("種子島の南はし", (1629, 2042), (30.3, 30.9, 130.8, 131.1), "south"),
    ],
}
INO_MIN_CP = 3.0                                   # 経緯線を追いかけるときの山の最小の強さ


def _ridge(im):
    """縦の細い線を浮かせる（左右25画素の平均 − 自分）"""
    from scipy import ndimage as ndi
    s = ndi.gaussian_filter1d(im, 1.0, axis=1)
    nb = (ndi.uniform_filter1d(im, 25, axis=1) * 25 - ndi.uniform_filter1d(im, 7, axis=1) * 7) / 18
    return np.clip(nb - s, 0, None)


def _track(R, guess, lo, hi, win=30, step=40):
    pts = []
    for t in range(lo, hi, step):
        a = int(round(guess(t)))
        seg = slice(max(a - win, 0), min(a + win + 1, R.shape[1]))
        if seg.stop - seg.start < 5:
            continue
        prof = R[t:t + step, seg].mean(0)
        j = int(np.argmax(prof))
        if prof[j] > INO_MIN_CP:
            idx = np.arange(len(prof))
            w = np.clip(prof - prof.max() * 0.4, 0, None)
            pts.append((t + step / 2, seg.start + (idx * w).sum() / w.sum()))
    return np.array(pts)


def _fit_line(pts):
    t, p = pts[:, 0], pts[:, 1]
    for _ in range(4):
        A = np.vstack([np.ones_like(t), t]).T
        c = np.linalg.lstsq(A, p, rcond=None)[0]
        r = p - A @ c
        keep = np.abs(r) < max(3 * np.std(r), 2.0)
        if keep.all():
            break
        t, p = t[keep], p[keep]
    return [float(c[0]), float(c[1])], float(np.std(r[keep])), int(keep.sum())


def ino_fit_grid(key):
    """経緯線を直線にあてはめる。緯線 y = a + b·x（緯度ごと）、経線 x = a + b·y（京都からの度数ごと）"""
    from PIL import Image
    im = np.asarray(Image.open(INO_FILES[key]).convert("L"), dtype=float)
    H, W = im.shape
    Rv = _ridge(im)
    Rh = _ridge(im.T).T
    g = INO_GRID[key]
    out = {"size": [W, H], "hl": {}, "vl": {}}
    for lat, y0 in g["hl"].items():
        pts = _track(Rh.T, lambda x, y0=y0: y0, 200, W - 200)
        co, sd, n = _fit_line(pts)
        out["hl"][str(lat)] = dict(co=co, sd=sd, n=n)
    for k, (x0, sl) in g["vl"].items():
        pts = _track(Rv, lambda y, x0=x0, sl=sl: x0 + sl * y, 300, H - 300)
        co, sd, n = _fit_line(pts)
        out["vl"][str(k)] = dict(co=co, sd=sd, n=n)
    return out


class InoMap:
    """伊能図の画素 ⇄ 緯度経度。緯線・経線の間を直線で補う"""

    def __init__(self, grid):
        self.lat_lines = sorted([(int(k), v["co"]) for k, v in grid["hl"].items()])          # (緯度, [a, b]) y = a + b x
        self.lon_lines = sorted([(int(k), v["co"]) for k, v in grid["vl"].items()])          # (京都からの度数, [a, b]) x = a + b y

    @staticmethod
    def _interp(vals, v):
        """vals: [(値, 位置)] 位置の昇順。位置 v が何の値か（外側は端の2本で延長）"""
        ps = [p for _k, p in vals]
        i = int(np.searchsorted(ps, v)) - 1
        i = max(0, min(len(vals) - 2, i))
        (k0, p0), (k1, p1) = vals[i], vals[i + 1]
        return k0 + (k1 - k0) * (v - p0) / (p1 - p0)

    def px_to_ll(self, x, y):
        lat_pos = sorted([(-k, a + b * x) for k, (a, b) in self.lat_lines], key=lambda z: z[1])     # y の昇順 = 緯度の降順
        lat = -self._interp(lat_pos, y)
        lon_pos = sorted([(k, a + b * y) for k, (a, b) in self.lon_lines], key=lambda z: z[1])
        k = self._interp(lon_pos, x)
        return lat, KYOTO_LON + k

    def ll_to_px(self, lat, lon):
        k = lon - KYOTO_LON
        x, y = 0.0, 0.0
        for _ in range(30):
            ys = sorted([(kk, a + b * x) for kk, (a, b) in self.lat_lines])
            y = self._interp_inv(ys, lat)
            xs = sorted([(kk, a + b * y) for kk, (a, b) in self.lon_lines])
            x = self._interp_inv(xs, k)
        return x, y

    @staticmethod
    def _interp_inv(vals, v):
        """vals: [(値, 位置)] 値の昇順。値 v の位置"""
        ks = [k for k, _p in vals]
        i = int(np.searchsorted(ks, v)) - 1
        i = max(0, min(len(vals) - 2, i))
        (k0, p0), (k1, p1) = vals[i], vals[i + 1]
        return p0 + (p1 - p0) * (v - k0) / (k1 - k0)


def modern_extreme(box, how):
    """今の地図（地球地図日本）の、範囲内で最も北／南／東／西の点 (lat, lon)"""
    lat0, lat1, lon0, lon1 = box
    pts = np.concatenate([xy for xy in read_coast_ll(lat0 - 0.2, lat1 + 0.2, lon0 - 0.2, lon1 + 0.2)])
    pts = pts[(pts[:, 1] >= lat0) & (pts[:, 1] <= lat1) & (pts[:, 0] >= lon0) & (pts[:, 0] <= lon1)]
    j = {"north": np.argmax(pts[:, 1]), "south": np.argmin(pts[:, 1]), "east": np.argmax(pts[:, 0]), "west": np.argmin(pts[:, 0])}[how]
    return float(pts[j, 1]), float(pts[j, 0])


def ino_measure():
    """位置合わせと、岬などの位置のずれ（伊能図の位置 − 今の位置。東・北が＋）を測る"""
    res = {"kyoto_lon": KYOTO_LON, "sheets": {}}
    for key in ("hokkaido", "kyushu"):
        grid = ino_fit_grid(key)
        m = InoMap(grid)
        pts = []
        for name, (px, py), box, how in INO_POINTS[key]:
            lat_t, lon_t = modern_extreme(box, how)
            lat_i, lon_i = m.px_to_ll(px, py)
            tx, ty = m.ll_to_px(lat_t, lon_t)
            ew = (lon_i - lon_t) * 111.19 * math.cos(math.radians(lat_t))
            ns = (lat_i - lat_t) * 111.19
            pts.append(dict(name=name, how=how, ino_px=[px, py], true_px=[float(tx), float(ty)], modern=[lat_t, lon_t], ino_ll=[lat_i, lon_i],
                            ew_km=float(ew), ns_km=float(ns), east=bool(ew > 0.5)))
        res["sheets"][key] = dict(grid=grid, points=pts)
    return res


def write_ino_md(res, path):
    L = ["# 伊能図（日本沿海輿地図・中図）の位置のずれ（動画の画面には km を出さない・確認用）", "",
         f"- 京都を通る経線（中度）を {res['kyoto_lon']}°E と置いた（図の「東X度／西X度」＝京都の経線からの度数）。**この置き方しだいで東西の値は一律に動く**（下の感度を参照）",
         "- 図の経緯線を直線にあてはめ（残差の標準偏差は下の表）、緯線・経線の間を直線で内挿して、岬などの画素を緯度経度に直した",
         "- 今の位置は 地球地図日本（国土地理院）の海岸線の、範囲内で最も北／南／東／西の点。伊能図の位置は画像を目で見て拾った画素（±10〜20画素＝約1〜2km）",
         "- ずれ＝伊能図の位置 − 今の位置。東西は東が＋、南北は北が＋（km）", ""]
    allew = []
    for key, name in (("hokkaido", "北海道東部（P-2906-1）"), ("kyushu", "九州南部（P-2906-8）")):
        sh = res["sheets"][key]
        L += [f"## {name}", "", "経緯線のあてはめ（標準偏差は画素。小さいほどよい）: " +
              "・".join(f"緯線{k}度 {v['sd']:.1f}" for k, v in sh["grid"]["hl"].items()) + " ／ " +
              "・".join(f"経線{k:+d} {v['sd']:.1f}" for k, v in ((int(a), b) for a, b in sh["grid"]["vl"].items())), "",
              "| 地点 | 今の位置（北緯, 東経） | 伊能図の位置（北緯, 東経） | 東西のずれ（km） | 南北のずれ（km） | 東にずれている |", "|---|---|---|---|---|---|"]
        for p in sh["points"]:
            L.append(f"| {p['name']} | {p['modern'][0]:.3f}, {p['modern'][1]:.3f} | {p['ino_ll'][0]:.3f}, {p['ino_ll'][1]:.3f} | {p['ew_km']:+.1f} | {p['ns_km']:+.1f} | {'はい' if p['east'] else 'いいえ'} |")
            allew.append(p["ew_km"])
        L.append("")
    hk = [q["ew_km"] for q in res["sheets"]["hokkaido"]["points"]]
    ky = [q["ew_km"] for q in res["sheets"]["kyushu"]["points"]]
    L += ["## まとめ", "", f"- 東西のずれ（東＋）: 最小 {min(allew):+.1f} km・最大 {max(allew):+.1f} km・平均 {sum(allew) / len(allew):+.1f} km（{len(allew)}地点）",
          f"- 東にずれている地点: {sum(1 for x in allew if x > 0.5)} / {len(allew)}（北海道東部 {min(hk):+.0f}〜{max(hk):+.0f} km・九州南部 {min(ky):+.0f}〜{max(ky):+.0f} km）",
          "- **感度**: 京都の経線の置き方を西へ 0.1°ずらす（135.67）と、東西のずれは北海道で約 8 km・九州で約 9.5 km 減る（東へずらすと同じだけ増える）。"
          "135.5 と置けば九州の岬・島は約 8〜11 km 西にずれ、東向きの矢印は出ない。つまり「東にずれている」は、基準の置き方（京都の経度）に左右される。",
          "- 北海道東部は九州南部より大きい。台本の「やや東にずれている」は九州にはちょうどよいが、北海道東部はそれより大きい。"
          "画面では km を出さず、矢印の長さ（実測のまま）で示す。知床岬は南北にも約 −20 km（伊能図のほうが南。画素の拾い方の誤差も含む）。"]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# ============================================================
# 3. 計算（下絵の main と同じ順序で乱数を引く）
# ============================================================
def _sub(mp, k=20):
    """画面用の見本 k 本（3点に1点）"""
    return [np.round(mp[j][::3], 2).tolist() for j in range(k)]


def compute():
    rng = np.random.default_rng(SEED)
    res = {"seed": SEED, "n": N, "route_km": float(CUM[-1]), "segments": int(len(DIST)), "true": np.round(TRUE[::3], 2).tolist(), "ladder": [], "star_interval": [], "degree": [], "params": []}
    for c, key in zip(LADDER, STEP_KEYS):
        mp = survey(rng, c, N)
        mean_e, end_e = stats(mp)
        q = np.percentile(mean_e, [10, 50, 90])
        dd = mp - TRUE[None]
        ew = np.median(np.abs(dd[..., 0]).mean(1))
        ns = np.median(np.abs(dd[..., 1]).mean(1))
        # 画面の見本: 先頭30本のうち、ずれが真ん中に近いものを先に
        sm = _sub(mp, 30)
        res["ladder"].append(dict(id=key, name=c["name"], p10=float(q[0]), p50=float(q[1]), p90=float(q[2]), end50=float(np.median(end_e)),
                                  ew=float(ew), ns=float(ns), mean_of_means=float(mean_e.mean()), samples=sm, sample_mean=[float(v) for v in mean_e[:30]],
                                  sample_dev=[np.round(np.hypot(*(mp[j] - TRUE).T)[::3], 2).tolist() for j in range(30)]))
        res["params"].append(dict(c, star=c["star"]))
        del mp, dd
    for ev in STAR_EVERY:
        c = dict(LADDER[3])
        c["star"] = dict(every_km=ev, err_km=0.9)
        mp = survey(rng, c, 2000)
        e, _ = stats(mp)
        res["star_interval"].append(dict(every_km=ev, p50=float(np.median(e)), samples=_sub(mp, 6)))
    for c in LADDER[1:5:3]:
        L, true_deg = degree_length(rng, c, N)
        q = np.percentile(L, [10, 50, 90])
        h, edges = np.histogram(L, bins=60, range=(104.0, 114.0))
        res["degree"].append(dict(name=c["name"], p10=float(q[0]), p50=float(q[1]), p90=float(q[2]), diff_pct=float(abs(q[1] - true_deg) / true_deg * 100),
                                  hist=h.tolist(), edges=[float(edges[0]), float(edges[-1])]))
    res["true_deg"] = R_EARTH * math.pi / 180
    # 第4章の画面用（別の乱数）: 星で直す前→後。同じ歩きで y だけ動く
    rp = np.random.default_rng(SEED_PAIR)
    a, b = survey_pair(rp, LADDER[3], 12)
    res["pair"] = dict(before=_sub(a, 12), after=_sub(b, 12),
                       mean_before=float(np.mean(np.hypot(*(a - TRUE[None]).transpose(2, 0, 1)))), mean_after=float(np.mean(np.hypot(*(b - TRUE[None]).transpose(2, 0, 1)))),
                       x_same=bool(np.allclose(a[..., 0], b[..., 0])))
    return res


# ============================================================
# 4. 照合（out/inoh-long/proto/tables.md と同じ値・段の単調・東西／南北・星の間隔・度）
# ============================================================
def _tables():
    txt = (OUT / "proto" / "tables.md").read_text(encoding="utf-8")
    rows = [r for r in txt.splitlines() if r.startswith("|")]
    nums = lambda s: [float(x) for x in re.findall(r"-?\d+\.\d+|-?\d+", s)]
    ladder, star, deg = [], [], []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        if re.match(r"^[0-4] ", cells[0]) and len(cells) == 6:
            ladder.append([nums(cells[1])[0], nums(cells[2]), nums(cells[3])[0], nums(cells[4])[0], nums(cells[5])[0]])
        elif re.match(r"^\d+ km ごと", cells[0]):
            star.append((nums(cells[0])[0], nums(cells[1])[0]))
        elif re.match(r"^[0-4] ", cells[0]) and len(cells) == 4:
            deg.append((nums(cells[1])[0], nums(cells[2]), nums(cells[3])[0]))
    return ladder, star, deg


def check(res):
    ladder, star, deg = _tables()
    out = []

    def A(name, ok):
        out.append((name, bool(ok)))
    L = res["ladder"]
    A("段が5つ・道すじ 1376km・1377区間・1万回", len(L) == 5 and round(res["route_km"]) == 1376 and res["segments"] == 1377 and res["n"] == 10000)
    for i, (row, st) in enumerate(zip(ladder, L)):
        A(f"段{i} 平均のずれ（真ん中）{st['p50']:.1f} km ＝ tables.md の {row[0]}", f"{st['p50']:.1f}" == f"{row[0]:.1f}")
        A(f"段{i} 1割〜9割 {st['p10']:.1f}〜{st['p90']:.1f} ＝ tables.md の {row[1][0]}〜{row[1][1]}", f"{st['p10']:.1f}" == f"{row[1][0]:.1f}" and f"{st['p90']:.1f}" == f"{row[1][1]:.1f}")
        A(f"段{i} 終点のずれ {st['end50']:.1f} km ＝ tables.md の {row[2]}", f"{st['end50']:.1f}" == f"{row[2]:.1f}")
        A(f"段{i} 東西 {st['ew']:.1f}・南北 {st['ns']:.1f} km ＝ tables.md の {row[3]}・{row[4]}", f"{st['ew']:.1f}" == f"{row[3]:.1f}" and f"{st['ns']:.1f}" == f"{row[4]:.1f}")
    p50 = [s["p50"] for s in L]
    A(f"段が進むたびに、ずれ（真ん中）が小さくなる（単調）: {[round(v, 1) for v in p50]}", all(a > b for a, b in zip(p50, p50[1:])))
    mm = [s["mean_of_means"] for s in L]
    A("段が進むたびに、1万回の平均も小さくなる（単調）", all(a > b for a, b in zip(mm, mm[1:])))
    A("台本の数字: 約50km（49.8）・24.4・8.3・3.1・2.2 ／ 東西 21.7・南北 36.7（段0）／ 19.1・10.0（段1）／ 2.9・7.3（段2）／ 2.9・0.7（段3）／ 1.9（段4）",
      [f"{L[0]['p50']:.0f}"] + [f"{s['p50']:.1f}" for s in L[1:]] == ["50", "24.4", "8.3", "3.1", "2.2"]
      and (f"{L[0]['ew']:.1f}", f"{L[0]['ns']:.1f}", f"{L[1]['ew']:.1f}", f"{L[1]['ns']:.1f}", f"{L[2]['ew']:.1f}", f"{L[2]['ns']:.1f}", f"{L[3]['ew']:.1f}", f"{L[3]['ns']:.1f}", f"{L[4]['ew']:.1f}")
      == ("21.7", "36.7", "19.1", "10.0", "2.9", "7.3", "2.9", "0.7", "1.9"))
    A("東西／南北: 段0は南北が大きい・段1で縮んだのはほとんど南北（東西はほぼそのまま）・段2で東西が縮む・段3で南北が0.7km・東西は動かない（2.9 → 2.9）",
      L[0]["ns"] > L[0]["ew"] and (L[0]["ns"] - L[1]["ns"]) > 5 * (L[0]["ew"] - L[1]["ew"]) and L[2]["ew"] < L[1]["ew"] / 5 and L[3]["ns"] < 1.0 and abs(L[3]["ew"] - L[2]["ew"]) < 0.1)
    A("台本: 「ほぼ半分」＝ 24.4/49.8 ＝ 0.49 ／「およそ3分の1」＝ 8.3/24.4 ＝ 0.34", 0.45 < L[1]["p50"] / L[0]["p50"] < 0.55 and 0.30 < L[2]["p50"] / L[1]["p50"] < 0.37)
    d_km = [L[0]["p50"] - L[1]["p50"], L[1]["p50"] - L[2]["p50"], L[2]["p50"] - L[3]["p50"], L[3]["p50"] - L[4]["p50"]]
    A(f"台本: 減ったkm「歩幅 約25km」「磁石 約16km」・いちばん多いのは歩幅（{[round(v, 1) for v in d_km]}）", int(math.floor(d_km[0] + 0.5)) == 25 and int(math.floor(d_km[1] + 0.5)) == 16 and d_km[0] == max(d_km))
    ratio = [1 - L[i + 1]["p50"] / L[i]["p50"] for i in range(4)]
    A(f"台本: 割合でいちばん減らしたのは磁石・星もほぼ同じ・縄・鎖は小さい（減った割合 {[round(v * 100) for v in ratio]}%）",
      ratio[1] == max(ratio) and abs(ratio[1] - ratio[2]) < 0.06 and ratio[2] > ratio[0] and ratio[3] < ratio[0])
    si = res["star_interval"]
    A(f"星の間隔 10/30/100/300km: 真ん中 {[round(s['p50'], 1) for s in si]} ＝ tables.md の {[v for _k, v in star]}", [f"{s['p50']:.1f}" for s in si] == [f"{v:.1f}" for _k, v in star])
    A("星の間隔: 間隔が長いほどずれは増える（単調）・どれも3km台（3.0〜3.99km）", all(a["p50"] <= b["p50"] for a, b in zip(si, si[1:])) and all(3.0 <= s["p50"] < 4.0 for s in si))
    dg = res["degree"]
    A(f"緯度1度（段1）{dg[0]['p50']:.2f} km・{dg[0]['p10']:.2f}〜{dg[0]['p90']:.2f}・差 {dg[0]['diff_pct']:.2f}% ＝ tables.md", f"{dg[0]['p50']:.2f}" == f"{deg[0][0]:.2f}" and f"{dg[0]['p10']:.2f}" == f"{deg[0][1][0]:.2f}" and f"{dg[0]['p90']:.2f}" == f"{deg[0][1][1]:.2f}" and f"{dg[0]['diff_pct']:.2f}" == f"{deg[0][2]:.2f}")
    A(f"緯度1度（段4）{dg[1]['p50']:.2f} km・{dg[1]['p10']:.2f}〜{dg[1]['p90']:.2f}・差 {dg[1]['diff_pct']:.2f}% ＝ tables.md", f"{dg[1]['p50']:.2f}" == f"{deg[1][0]:.2f}" and f"{dg[1]['p10']:.2f}" == f"{deg[1][1][0]:.2f}" and f"{dg[1]['p90']:.2f}" == f"{deg[1][1][1]:.2f}" and f"{dg[1]['diff_pct']:.2f}" == f"{deg[1][2]:.2f}")
    A("台本の1度の長さ: 110.0（1%ほど小さい）・111.2・この球の1度 111.19km", f"{dg[0]['p50']:.1f}" == "110.0" and f"{dg[1]['p50']:.1f}" == "111.2" and f"{res['true_deg']:.2f}" == "111.19" and 0.9 < dg[0]["diff_pct"] < 1.2)
    A("忠敬の値 28.2里 ＝ 約110.75km（1里＝3.927km）・今の値 約110.95km・差 0.2%ほど", abs(28.2 * 3.92727 - 110.75) < 0.01 and abs((110.95 - 110.75) / 110.95 * 100 - 0.2) < 0.05)
    pr = res["pair"]
    A(f"第4章の画面用の見本（星で直す前→後）: 同じ歩きで x は同じ・平均のずれは前 {pr['mean_before']:.1f} → 後 {pr['mean_after']:.1f} km に縮む", pr["x_same"] and pr["mean_after"] < pr["mean_before"] / 1.5)
    A("見本: 各段30本・点の数が同じ（460点＝3点に1点）・道すじ（紺の線）も同じ点数", all(len(s["samples"]) == 30 and len(s["samples"][0]) == len(res["true"]) for s in L))
    bad = [name for name, ok in out if not ok]
    for name, ok in out:
        print(("  OK  " if ok else "  NG  ") + name)
    if bad:
        raise SystemExit(f"照合に失敗: {bad}")
    print(f"照合 {len(out)} 件 OK")
    return out


# ============================================================
# 5. numbers.md
# ============================================================
def write_numbers(res, checks, ino):
    L = res["ladder"]
    rows = ["# 数字（伊能忠敬ロング・sims/inoh-long.py --numbers が書く。手で直さない）", "",
            f"道すじ {res['route_km']:.0f} km（{res['segments']} 区間）・{res['n']:,} 回・乱数の種 {res['seed']}・下絵の海岸線は地球地図日本（国土地理院）", "",
            "## ずれ（真ん中の回）", "",
            "| 段 | 平均のずれ（真ん中） | 1割〜9割 | 終点のずれ（真ん中） | 東西のずれ | 南北のずれ |", "|---|---|---|---|---|---|"]
    for s in L:
        rows.append(f"| {s['name']} | {s['p50']:.1f} km | {s['p10']:.1f}〜{s['p90']:.1f} km | {s['end50']:.1f} km | {s['ew']:.1f} km | {s['ns']:.1f} km |")
    rows += ["", "## 減ったkmと減った割合（前の段から）", "", "| 段 | 減ったkm | 減った割合 |", "|---|---|---|"]
    for i in range(1, 5):
        rows.append(f"| {L[i]['name']} | {L[i - 1]['p50'] - L[i]['p50']:.1f} km | {(1 - L[i]['p50'] / L[i - 1]['p50']) * 100:.0f}% |")
    rows += ["", "## 星を見る間隔（段3の条件で間隔だけ変える・各2000回）", "", "| 間隔 | 平均のずれ（真ん中） |", "|---|---|"]
    for s in res["star_interval"]:
        rows.append(f"| {s['every_km']:.0f} km ごと | {s['p50']:.1f} km |")
    rows += ["", f"## 緯度1度の長さ（江戸から約600km北・本当の1度は {res['true_deg']:.2f} km）", "", "| 段 | 真ん中 | 1割〜9割 | 本当の値との差（%） |", "|---|---|---|---|"]
    for s in res["degree"]:
        rows.append(f"| {s['name']} | {s['p50']:.2f} km | {s['p10']:.2f}〜{s['p90']:.2f} km | {s['diff_pct']:.2f}% |")
    rows += ["", "資料の値（置いたのではない）: 忠敬の1度 28.2里≒110.75km／今の値 約110.95km／差 約0.2%", "",
             "## 照合（out/inoh-long/proto/tables.md と同じ・単調・東西／南北）", ""] + [f"- {'OK' if ok else 'NG'} {name}" for name, ok in checks]
    rows += ["", f"照合 {len(checks)} 件 OK", "", "## 伊能図の位置のずれ（km は画面に出さない。詳しくは ino_offsets.md）", ""]
    for key in ("hokkaido", "kyushu"):
        for p in ino["sheets"][key]["points"]:
            rows.append(f"- {p['name']}: 東西 {p['ew_km']:+.1f} km・南北 {p['ns_km']:+.1f} km")
    (OUT / "numbers.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("numbers.md:", OUT / "numbers.md")


CREDIT_COAST = "海岸線: 地球地図日本（国土地理院）をもとに、めでたしかめが作成"
CREDIT_COAST_URL = "https://www.gsi.go.jp/kankyochiri/gm_jpn.html"
CREDIT_INO = "日本沿海輿地図（中図）北海道東部／九州南部　東京国立博物館所蔵　出典: ColBase"
CREDIT_INO_URLS = ["https://colbase.nich.go.jp/collection_items/tnm/P-2906-1", "https://colbase.nich.go.jp/collection_items/tnm/P-2906-8"]


def write_credits():
    txt = [f"{CREDIT_COAST}（縮尺を変え、線を間引いて描いています）{CREDIT_COAST_URL}",
           f"{CREDIT_INO}（画像を縮小して表示）",
           f"ColBase（{CREDIT_INO_URLS[0]}）をもとにめでたしかめ作成",
           f"ColBase（{CREDIT_INO_URLS[1]}）をもとにめでたしかめ作成"]
    (OUT / "credits.txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print("credits.txt:", OUT / "credits.txt")


# ============================================================
# 6. 保存・読み込み・CLI
# ============================================================
def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def save(res):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(_jsonable(res), ensure_ascii=False), encoding="utf-8")


def load():
    return json.loads((OUT / "data.json").read_text(encoding="utf-8"))


def do_ino():
    ino = ino_measure()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ino_reg.json").write_text(json.dumps(_jsonable(ino), ensure_ascii=False, indent=1), encoding="utf-8")
    write_ino_md(ino, OUT / "ino_offsets.md")
    for key in ("hokkaido", "kyushu"):
        for p in ino["sheets"][key]["points"]:
            print(f"  {p['name']}: 東西 {p['ew_km']:+.1f} km・南北 {p['ns_km']:+.1f} km")
    print("ino_offsets.md:", OUT / "ino_offsets.md")
    return ino


_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers", "--md", "--ino"))
if __name__ == "__main__" and _MODEL_CLI:
    args = sys.argv[1:]
    if "--ino" in args and "--numbers" not in args:
        do_ino()
        raise SystemExit
    if "--numbers" in args:
        print("計算します（1〜2分）…", flush=True)
        res = _jsonable(compute())
        save(res)
        res = load()
    else:
        res = load()
    chk = check(res)
    if "--numbers" in args:
        ino = do_ino()
        write_numbers(res, chk, ino)
        write_credits()
    raise SystemExit


# ==== 場面 ====

# ####################################################################################################
# ここから下は場面（描画・音・照合・書き出し）。2026-10-23 追加（モデルの計算は変えていない）。
# 台本: publish/inoh-long/narration_B.md の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 形と部品は sims/okehazama-long.py・sims/densha-long.py の場面部分（見開きノート・付せん・数字の欄・章カード・終了画面・照合）。
#
# 使い方
#   python -X utf8 sims/inoh-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/inoh-long.py --stills --fake-voice        要所の静止画と sheet_480.png・ch6_compare_480.png（out/inoh-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
#   python -X utf8 sims/inoh-long.py --wraps --fake-voice         字幕の折り返しを全部表示
#   python -X utf8 sims/inoh-long.py --readings --fake-voice      読みの確認（scene_work/readings.log）
#   python -X utf8 sims/inoh-long.py --docs --fake-voice          文字起こし・チャプター（scene_work/）
#   python -X utf8 sims/inoh-long.py --preview                    960×540 の確認用動画（AivisSpeech の音声）
#   （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
# ####################################################################################################
import re as _re
from bisect import bisect_left, bisect_right
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (beat, bell, blip, check_answers, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh)
from engine.note import INK, MARKER, PAPER, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

FAKE = "--fake-voice" in sys.argv
VOICE_DIR = OUT / "voice"
WORK = OUT / "scene_work"


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本の読み込み（narration_B.md の「- 」の行。文言は一字も変えない）
#   「- （無音 3秒・…）」＝声のない区間（Gap） ／ 「- （…）」「- 〔…〕」だけの行＝画面の指示（声にしない）
#   行の終わりの〔…〕＝その文のときの画面の絵（声にしない）
# ============================================================
NARR_PATH = ROOT / "publish" / SLUG / "narration_B.md"
G_DEFAULT = {1: 5.0, 2: 5.0, 3: 5.0, 4: 5.0, 5: 5.0, 7: 6.0}          # 「無音」に秒数が書いていない区間の長さ


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
            mn = _re.search(r"〔([^〕]*)〕\s*$", body)
            txt = (body[:mn.start()] if mn else body).strip()
            cur["items"].append(("line", txt, mn.group(1) if mn else ""))
    return chaps


CHAPS = parse_narration()
CH_TITLES = [c["title"] for c in CHAPS]
LINES = {}                         # 文の id -> (章, 文)
LINE_NOTE = {}                     # 文の id -> 〔画面の絵〕
GAP_NOTE = {}                      # 無音の id -> 注
CH_NOTE0 = {}                      # 章の最初の画面指示（（…）〔…〕のみの行）
SPEED_V = 1.0

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
    return out


def _items():
    C, G = lf.Chapter, lf.Gap
    out = []
    for ch in CHAPS:
        n = ch["n"]
        out.append(C(ch["title"], id=f"ch{n}", gap=0.0 if n == 0 else 1.0))
        lines = [it for it in ch["items"] if it[0] == "line"]
        k, li = 0, 0
        for kind, val, note_ in ch["items"]:
            if kind == "line":
                li += 1
                for j, part in enumerate(split_long(val)):          # 字幕が2行に収まらない文は、文言を変えずに「。」で2つの Line に分ける
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and part is split_long(val)[-1]
                    out.append(lf.Line(lid, part, pause=0.3 if n == 0 else (0.6 if last else 0.35), speed=SPEED_V))      # 0章（最初の約60秒）は、どの文のあとも約0.3秒
            elif kind == "gap":
                gid = f"g{n}"
                GAP_NOTE[gid] = note_
                out.append(G(gid, val if val else G_DEFAULT[n]))
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


VOICE_PAUSES = (0.10, 0.22)
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
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# ============================================================
# 小さな道具（okehazama-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"
GREEN = "#3f9a6a"
ORANGE = "#ec8a2e"                                   # 描いた線（だいだい）
NAVY = INK                                           # 本当の線（紺）
COAST_C = "#3b5a94"                                  # 今の海岸線（紺・うすめ）


def lerp(a, b, u):
    return a + (b - a) * u


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


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
    """白い下地つきの札。align='left' なら x は左端"""
    if a <= 0.003 or progress <= 0:
        return 0
    w = text_width(s, size) + 26
    cx = x + w / 2 - 13 if align == "left" else x
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, cx - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, cx, y, size, col, progress, align="center", alpha=a)
    return w


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
INO = json.loads((OUT / "ino_reg.json").read_text(encoding="utf-8"))
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ---- 場面の合図: 文の一部（手がかり）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    "c0_q": (0, "目分量で描いた地図は"), "c0_ino": (0, "伊能忠敬は"), "c0_n": (0, "1万回ためします"), "c0_y": (0, "1800年"),
    "c0_e": (0, "南東の海ぞい"), "c0_d": (0, "足していくことで"), "c0_z": (0, "「ずれ」と呼びます"), "c0_i": (0, "ひとつずつ足して"),
    "c1_0": (1, "この章では"), "c1_o": (1, "忠敬のやり方ではありません"), "c1_m": (1, "方位と呼びます"), "c1_p": (1, "150mほど"),
    "c1_r": (1, "ちょうど真ん中"), "c1_ew": (1, "東西と南北に分けて"), "c1_ns": (1, "南北は、約37km"), "c1_end": (1, "分かったことです"),
    "c2_0": (2, "この章では"), "c2_def": (2, "歩測とは"), "c2_69": (2, "約69cm"), "c2_c": (2, "歩測が中心"), "c2_50": (2, "50mほど"),
    "c2_r": (2, "真ん中の回"), "c2_half": (2, "ほぼ半分"), "c2_ns": (2, "ほとんど南北"), "c2_n2": (2, "南北は10.0km"), "c2_front": (2, "道の前半"), "c2_end": (2, "分かったことです"),
    "c3_0": (3, "この章では"), "c3_stick": (3, "杖の先に磁針"), "c3_6": (3, "細かさまで読めました"), "c3_03": (3, "0.3度"), "c3_r": (3, "真ん中の回"),
    "c3_third": (3, "3分の1"), "c3_dist": (3, "距離のずれは、線を"), "c3_dir": (3, "向きのずれは、線を曲げて"),
    "c3_whole": (3, "地図全体に響きます"), "c3_km25": (3, "約25km"), "c3_km16": (3, "約16km"), "c3_ratio": (3, "の大きさに対する割合"), "c3_ew": (3, "東西は2.9km"), "c3_ns": (3, "7.3kmまで減りました"), "c3_end": (3, "分かったことです"),
    "c4_0": (4, "この章では"), "c4_lat": (4, "緯度と言います"), "c4_low": (4, "真南の星は低く"), "c4_quad": (4, "象限儀"), "c4_09": (4, "0.9km"),
    "c4_30": (4, "30kmごと"), "c4_redraw": (4, "描き直します"), "c4_r": (4, "真ん中の回"), "c4_ns": (4, "南北のずれは、7.3km"), "c4_ew": (4, "東西のずれは、2.9km"), "c4_end": (4, "分かったことです"),
    "c5_0": (5, "この章では"), "c5_rope": (5, "麻の縄"), "c5_if": (5, "もし縄や鎖で"), "c5_10": (5, "10mほど"), "c5_r": (5, "真ん中の回"), "c5_ew": (5, "2.9kmから1.9km"), "c5_end": (5, "分かったことです"),
    "c6_0": (6, "この章では"), "c6_lat": (6, "緯度、つまり南北"), "c6_same": (6, "同じ緯度なら"), "c6_time": (6, "同じ星が真南に来る時刻"), "c6_clock": (6, "持ち運んでも"),
    "c6_then": (6, "足していくしかありません"), "c6_look": (6, "次に、実際の伊能図"), "c6_museum": (6, "東京国立博物館にある"),
    "c6_east": (6, "東にずれています"), "c6_big": (6, "東へ行くほど"), "c6_weak": (6, "東西が弱い"), "c6_but": (6, "ただ、実物のずれ"), "c6_why": (6, "以外にも、原因"), "c6_kyu": (6, "九州も、同じ向き"), "c6_end": (6, "分かったことです"),
    "c7_def": (7, "とは、北へ進んで"), "c7_b2": (7, "111.2km"), "c7_ball": (7, "ほぼ戻ります"), "c7_b3": (7, "約110.75km"), "c7_b4": (7, "約110.95km"),
    "c8_1": (8, "工夫をひとつずつ足すと"), "c8_ratio": (8, "割合でいちばん減らした"), "c8_km": (8, "で多かったのは"), "c8_ew": (8, "東西のずれが残りました"),
    "c8_mt": (8, "遠くの山"), "c8_cond": (8, "数字は、この道すじを"), "c8_end": (8, "分かったことです"), "c8_q": (8, "あなたなら"), "c8_ch": (8, "このチャンネルでは"), "c8_sub": (8, "よければ"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


def Mk(k, f=0.5):
    return mid(ID[k], f)





# ============================================================
# 地図の座標（km → 画面）と、地図の下絵（海岸線・本当の道すじ）。下絵は1枚に描いて貼る
# ============================================================
LBOX = (45, 36, 935, 936)                            # 左ページの絵の箱
_xs, _ys = TRUE[:, 0], TRUE[:, 1]
MX0, MX1 = float(_xs.min()) - 70, float(_xs.max()) + 70
MY0, MY1 = float(_ys.min()) - 60, float(_ys.max()) + 95
MS = min((LBOX[2] - 410) / (MX1 - MX0), (LBOX[3] - LBOX[1] - 4) / (MY1 - MY0))      # 1km あたりの画素
MOX = LBOX[2] - (MX1 - MX0) * MS
MOY = float(LBOX[3])


def mpx(x, y):
    return MOX + (x - MX0) * MS, MOY - (y - MY0) * MS


def to_px(arr):
    a = np.asarray(arr, float)
    return np.stack([MOX + (a[:, 0] - MX0) * MS, MOY - (a[:, 1] - MY0) * MS], 1)


TRUE_PX = to_px(RES["true"])                          # 本当の道すじ（3点に1点）
LAD = {st["id"]: st for st in RES["ladder"]}
SAMP = {k: [to_px(s_) for s_ in LAD[k]["samples"]] for k in STEP_KEYS}
STAR_SAMP = [[to_px(s_) for s_ in si["samples"]] for si in RES["star_interval"]]
PAIR_B = [to_px(s_) for s_ in RES["pair"]["before"]]
PAIR_A = [to_px(s_) for s_ in RES["pair"]["after"]]
VAL = {k: LAD[k]["p50"] for k in STEP_KEYS}


def med_idx(k):
    """見本30本のうち、平均のずれが真ん中（p50）にいちばん近い回"""
    d = [abs(v - LAD[k]["p50"]) for v in LAD[k]["sample_mean"]]
    return int(np.argmin(d))


def open_idx():
    """冒頭に描く1回: 段0の見本のうち、平均が40〜75kmで、道すじの半分でいちばん大きく離れるもの"""
    best, bv = 0, -1.0
    for j in range(30):
        dv = LAD["L0"]["sample_dev"][j]
        m = LAD["L0"]["sample_mean"][j]
        if 45 <= m <= 80 and dv[int(len(dv) * 0.55)] > bv:
            best, bv = j, dv[len(dv) // 2]
    return best


OPEN_J = open_idx()
OPEN_DEV = LAD["L0"]["sample_dev"][OPEN_J]            # その回の、点ごとの本当の位置からの距離（km）


def _coast_px(lat0=34.4, lat1=44.6, lon0=138.0, lon1=146.6):
    return [to_px(ln) for ln in read_coast(lat0, lat1, lon0, lon1)]


COAST_PX = _coast_px()
_BASE = {}


def draw_poly(ctx, p, w, col, a, n=None, cap=cairo.LINE_CAP_ROUND):
    if a <= 0.003 or len(p) < 2:
        return
    n = len(p) if n is None else max(0, min(len(p), int(n)))
    if n < 2:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*p[0])
    for q in p[1:n]:
        ctx.line_to(*q)
    ctx.stroke()


def base_surface():
    """今の海岸線（うすい紺）と、本当の道すじ（濃い紺）。1枚に描いて貼る"""
    if "map" not in _BASE:
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, lf.W, lf.H)
        c = cairo.Context(s)
        c.rectangle(LBOX[0], LBOX[1], LBOX[2] - LBOX[0], LBOX[3] - LBOX[1])
        c.clip()
        for p in COAST_PX:
            draw_poly(c, p, 3.0, COAST_C, 0.55)
        draw_poly(c, TRUE_PX, 6.0, NAVY, 1.0)
        _BASE["map"] = s
    return _BASE["map"]


def paint_base(ctx, a=1.0):
    ctx.set_source_surface(base_surface(), 0, 0)
    ctx.paint_with_alpha(a)


def draw_bundle(ctx, step, a=1.0, n=24, alpha=0.30, w=3.4, med=False):
    for p in SAMP[step][:n]:
        draw_poly(ctx, p, w, ORANGE, alpha * a)
    if med:
        draw_poly(ctx, SAMP[step][med_idx(step)], 6.0, ORANGE, 0.95 * a)


def bundle_grow(ctx, step, t, t0, t1, n=20, wd=1.3, alpha=0.30, w=3.4):
    """無音の早回し: 1回ぶんの地図が江戸から北へ引かれていくのを、次々に重ねる（1万回の早回し）"""
    stagger = (t1 - t0 - wd) / (n - 1)
    for i in range(n):
        pr = clamp01((t - t0 - i * stagger) / wd)
        if pr > 0:
            p = SAMP[step][i]
            draw_poly(ctx, p, w, ORANGE, alpha, n=pr * (len(p) - 1) + 1)


def bundle_grow_pair(ctx, t, t0, t1, n=12):
    """第4章の早回し: 星で直す前の束が、南北だけ動いて本当の線に吸いつく（x は同じ・y だけ動く）"""
    u = ease_in_out(clamp01((t - t0 - 0.3) / max(0.5, t1 - t0 - 1.0)))
    for i in range(n):
        b, a_ = PAIR_B[i], PAIR_A[i]
        draw_poly(ctx, b + (a_ - b) * u, 3.4, ORANGE, 0.34)


# ---- 後ろ姿の旅人（杖つき・顔は描かない）と足あと ----
def walker(ctx, x, y, h, a=1.0, step=0.0, staff=True):
    """(x, y)=足元の中心。後ろから見た旅人。笠・荷・杖（先に方位盤）。顔は描かない"""
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    lw = max(2.5, h * 0.016)
    sw = math.sin(step)
    ink = hexrgb(INK, a)

    def line(x0, y0, x1, y1, w, col):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.set_line_width(w)
        ctx.move_to(x0 * h, y0 * h)
        ctx.line_to(x1 * h, y1 * h)
        ctx.stroke()
    if staff:                                          # 杖（右手）。先に方位盤
        line(0.20, 0.0, 0.20, -1.04, h * 0.026, "#9a6a38")
        ctx.set_source_rgba(*hexrgb("#fff7e0", a))
        ctx.arc(0.20 * h, -1.10 * h, 0.075 * h, 0, 6.2832)
        ctx.fill_preserve()
        ctx.set_source_rgba(*ink)
        ctx.set_line_width(lw)
        ctx.stroke()
        line(0.20, -1.15, 0.20, -1.05, h * 0.016, RED)
    line(-0.05, -0.40, -0.07 - 0.03 * sw, -0.02, h * 0.07, "#3d4a66")      # 足
    line(0.05, -0.40, 0.07 + 0.03 * sw, -0.02, h * 0.07, "#3d4a66")
    for sgn, off in ((-1, -0.03 * sw), (1, 0.03 * sw)):
        ctx.set_source_rgba(*hexrgb("#d6c19a", a))
        ctx.save()
        ctx.translate((sgn * 0.07 + off) * h, -0.015 * h)
        ctx.scale(1.0, 0.45)
        ctx.arc(0, 0, 0.055 * h, 0, 6.2832)
        ctx.fill()
        ctx.restore()
    ctx.set_source_rgba(*hexrgb("#c9a56a", a))                                 # 荷（背中）
    rrect(ctx, -0.115 * h, -0.80 * h, 0.23 * h, 0.22 * h, h * 0.03)
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#35507f", a))                                 # 着物の背中
    ctx.move_to(-0.15 * h, -0.84 * h)
    ctx.line_to(0.15 * h, -0.84 * h)
    ctx.line_to(0.17 * h, -0.36 * h)
    ctx.line_to(-0.17 * h, -0.36 * h)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()
    line(0.0, -0.84, 0.0, -0.40, h * 0.012, "#1f3254")
    line(-0.115, -0.80, -0.14, -0.58, h * 0.014, "#7a5a2a")                  # 荷のひも
    line(0.115, -0.80, 0.14, -0.58, h * 0.014, "#7a5a2a")
    line(-0.15, -0.80, -0.19, -0.58 + 0.02 * sw, h * 0.05, "#35507f")          # 腕（左は振り・右は杖へ）
    line(0.15, -0.80, 0.20, -0.64, h * 0.05, "#35507f")
    ctx.set_source_rgba(*hexrgb("#2b2b33", a))                                 # 頭（後ろ）と笠
    ctx.arc(0, -0.895 * h, 0.07 * h, 0, 6.2832)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#d6c19a", a))
    ctx.move_to(-0.19 * h, -0.90 * h)
    ctx.line_to(0.0, -1.04 * h)
    ctx.line_to(0.19 * h, -0.90 * h)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*ink)
    ctx.set_line_width(lw)
    ctx.stroke()
    ctx.restore()


def footprints(ctx, path_px, n_end, spacing=34.0, a=0.55, size=9.0):
    """道すじ（画面の点列）の最初から n_end 番目までに、左右交互の足あとを置く"""
    p = np.asarray(path_px)[:max(2, int(n_end))]
    if len(p) < 2:
        return
    seg = np.hypot(*np.diff(p, axis=0).T)
    cum = np.concatenate([[0], np.cumsum(seg)])
    k = 0
    for d in np.arange(spacing, cum[-1], spacing):
        i = int(np.searchsorted(cum, d)) - 1
        i = max(0, min(len(seg) - 1, i))
        u = (d - cum[i]) / max(seg[i], 1e-6)
        pt = p[i] + (p[i + 1] - p[i]) * u
        ang = math.atan2(p[i + 1][1] - p[i][1], p[i + 1][0] - p[i][0])
        side = 1 if k % 2 else -1
        k += 1
        ox, oy = -math.sin(ang) * side * 9, math.cos(ang) * side * 9
        ctx.save()
        ctx.translate(pt[0] + ox, pt[1] + oy)
        ctx.rotate(ang)
        ctx.scale(1.5, 1.0)
        ctx.arc(0, 0, size * 0.62, 0, 6.2832)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#6e5c3e", a))
        ctx.fill()


def star_shape(ctx, x, y, r, col, a=1.0, lw=3.0):
    ctx.set_source_rgba(*hexrgb(col, a))
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        ang = -math.pi / 2 + k * math.pi / 5
        (ctx.move_to if k == 0 else ctx.line_to)(x + rr * math.cos(ang), y + rr * math.sin(ang))
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(lw)
    ctx.stroke()


def arrow_line(ctx, x0, y0, x1, y1, col, w=6.0, a=1.0, head=22.0, both=False):
    ang = math.atan2(y1 - y0, x1 - x0)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(x1 - math.cos(ang) * head * 0.6, y1 - math.sin(ang) * head * 0.6)
    ctx.stroke()
    ends = [(x1, y1, ang)] + ([(x0, y0, ang + math.pi)] if both else [])
    for ex, ey, an in ends:
        ctx.move_to(ex, ey)
        ctx.line_to(ex - head * math.cos(an - 0.45), ey - head * math.sin(an - 0.45))
        ctx.line_to(ex - head * math.cos(an + 0.45), ey - head * math.sin(an + 0.45))
        ctx.close_path()
        ctx.fill()


def dotted_line(ctx, x0, y0, x1, y1, col, w=5.0, a=1.0, dash=(4.0, 12.0)):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_dash(list(dash))
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    ctx.set_dash([])


def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 910)
    ctx.clip()


# ============================================================
# 左ページ（絵）。時刻つきの「層」を重ねる（出入りは 0.4秒のフェード）
# ============================================================
T_WALK = 9.0                                         # 冒頭: 歩く点が江戸から北へ道すじを歩ききる秒数
SX = 52                                              # 左の細い帯（地図の左）に置く札の左端
EDO_PX = (float(TRUE_PX[0][0]), float(TRUE_PX[0][1]))


CREDIT_LINES = ["海岸線: 地球地図日本", "（国土地理院）をもとに、", "めでたしかめが作成"]        # つなぐと CREDIT_COAST
CREDIT_SIZE = 32                                                                      # 1920幅で32px（28px以上）
CREDIT_T0, CREDIT_T1 = Sk("c0_e", 0.3), Sk("c0_z", 0.0)                              # 出す時刻（「南東の海ぞい」の文の途中〜「ずれ」と呼ぶ文のはじめ）
CREDIT_BOX = (48, 712, 48 + int(max(text_width(l_, CREDIT_SIZE) for l_ in CREDIT_LINES)) + 30, 852)   # 左ページの左下。凡例（y<700）と「江戸」の札（y>860）のあいだ


def L_title(ctx, t, a=1.0):
    """0秒目から題字「伊能忠敬」（左上）"""
    text(ctx, "伊能忠敬", 62, 104, 112, INK, align="left", alpha=a)
    pen_line(ctx, 58, 174, 62 + text_width("伊能忠敬", 112) + 8, 168, RED, seed=3, width=9, progress=clamp01(t / 0.6), alpha=a)


def legend_map(ctx, a=1.0, y=600):
    """紺＝本当の道すじ・だいだい＝描いた線"""
    if a <= 0.003:
        return
    ctx.set_source_rgba(1, 1, 1, 0.8 * a)
    rrect(ctx, SX - 4, y - 32, 320, 120, 10)
    ctx.fill()
    draw_poly(ctx, np.array([[SX + 6, y], [SX + 58, y]]), 7, NAVY, a)
    text(ctx, "本当の道すじ", SX + 72, y, 40, INK, align="left", alpha=a)
    draw_poly(ctx, np.array([[SX + 6, y + 56], [SX + 58, y + 56]]), 7, ORANGE, a)
    text(ctx, "描いた線", SX + 72, y + 56, 40, INK, align="left", alpha=a)


def strip_tag(ctx, t, key, s, y, col=INK, size=52, off=0.15, frac=0.0, until=None):
    """左の帯の札。台本の文（手がかり key）から現れる"""
    t0 = Sk(key, frac) + off
    if t < t0:
        return 0
    a = fade(t, t0, 0.3)
    if until is not None:
        a *= out_fade(t, until, 0.3)
    return tag(ctx, s, SX, y, size, col, a, align="left")


def L_ch0(ctx, t):
    """冒頭〜0章: 紺の本当の道すじ（と今の海岸線）。後ろ姿の旅人が江戸から北へ歩き、だいだいの線を引く。線は本当の道すじからどんどん離れる"""
    paint_base(ctx)
    p = SAMP["L0"][OPEN_J]
    u = clamp01(t / T_WALK)
    n = u * (len(p) - 1) + 1
    draw_poly(ctx, p, 7.0, ORANGE, 0.95, n=n + 1)
    footprints(ctx, p, n, spacing=26.0, a=0.5)
    # 歩ききったあとも、別の回が次々に引かれる（無音の区間はなくなったので、声の文の下でそのまま続く）
    g0 = T_WALK + 0.3
    for i in range(1, 7):
        pr = clamp01((t - g0 - (i - 1) * 0.28) / 1.3)
        if pr > 0:
            q = SAMP["L0"][(OPEN_J + i) % 30]
            draw_poly(ctx, q, 4.0, ORANGE, 0.36, n=pr * (len(q) - 1) + 1)
    # 旅人（頭の位置）
    i0 = int(min(len(p) - 1, n))
    wa = out_fade(t, T_WALK + 2.5, 0.5)
    if wa > 0.003:
        walker(ctx, p[i0][0], p[i0][1] + 4, 128, wa, step=t * 7.0)
    tag(ctx, "江戸", EDO_PX[0] - 82, EDO_PX[1] - 6, 44, INK, 1.0)
    if t >= Sk("c0_e", 0.0):
        px_h = mpx(*to_xy(43.9, 142.9))
        tag(ctx, "北海道", px_h[0], px_h[1], 44, INK, fade(t, Sk("c0_e", 0.0), 0.3))
    legend_map(ctx, fade(t, Sk("c0_n", 0.0) + 2.6, 0.4))                # 大きな旅人が消えたあとに凡例
    ca = fade(t, CREDIT_T0, 0.4) * out_fade(t, CREDIT_T1, 0.4)         # 海岸線の出典（1回だけ）
    if ca > 0.003:
        ctx.set_source_rgba(1, 1, 1, 0.92 * ca)
        rrect(ctx, CREDIT_BOX[0], CREDIT_BOX[1], CREDIT_BOX[2] - CREDIT_BOX[0], CREDIT_BOX[3] - CREDIT_BOX[1], 10)
        ctx.fill()
        for k_, ln_ in enumerate(CREDIT_LINES):
            text(ctx, ln_, CREDIT_BOX[0] + 14, 740 + 40 * k_, CREDIT_SIZE, INK, align="left", alpha=ca)


def L_walk_big(ctx, t):
    """0章: 「後ろ姿・杖・足あと」。左の帯に大きな旅人（顔は描かない）と足あと"""
    walker(ctx, 215, 835, 440, 1.0, step=t * 3.0)
    path = np.array([[330 - 100 * k / 12, 935 - 90 * k / 12] for k in range(13)])
    footprints(ctx, path, 13, spacing=38.0, a=0.6, size=14.0)


def L_map(ctx, t, step, grow=None, med=False, bundle=True, tags=()):
    """地図に、その段の束（だいだい）を重ねる。grow=(t0, t1) なら無音の早回し（次々に重なる）"""
    paint_base(ctx)
    if grow and t < grow[1]:
        bundle_grow(ctx, step, t, grow[0], grow[1])
    elif bundle:
        draw_bundle(ctx, step, 1.0, n=24, alpha=(0.16 if med else 0.30), med=med)
    legend_map(ctx, 1.0)


# ---- ch1: 1区間（距離と方位）----
def L_seg1(ctx, t):
    O = (330.0, 790.0)
    th = math.radians(35.0)
    L = 420.0
    P = (O[0] + L * math.sin(th), O[1] - L * math.cos(th))
    th2 = math.radians(70.0)
    Q = (P[0] + 330 * math.sin(th2), P[1] - 330 * math.cos(th2))
    t0 = Sk("c1_m", 0.0)
    a = fade(t, t0, 0.4)
    text(ctx, "1kmごとに 測る", LCX, 120, 60, INK, alpha=a)
    dotted_line(ctx, O[0], O[1], O[0], 300, INK, 4.0, a * 0.8)
    text(ctx, "北", O[0], 262, 52, INK, alpha=a)
    arrow_line(ctx, O[0], O[1], P[0], P[1], ORANGE, 9.0, a * fade(t, t0 + 0.6, 0.5), 30.0)
    # 方位（北からの角度）
    ctx.set_source_rgba(*hexrgb(RED, a * fade(t, t0 + 1.6, 0.5)))
    ctx.set_line_width(6)
    ctx.arc(O[0], O[1], 170, -math.pi / 2, -math.pi / 2 + th)
    ctx.stroke()
    text(ctx, "方位", O[0] + 70, O[1] - 235, 56, RED, alpha=a * fade(t, t0 + 1.6, 0.5))
    text(ctx, "（向き）", O[0] + 70, O[1] - 175, 44, RED, bold=False, alpha=a * fade(t, t0 + 1.6, 0.5))
    text(ctx, "距離", (O[0] + P[0]) / 2 + 95, (O[1] + P[1]) / 2 + 20, 56, ORANGE, alpha=a * fade(t, t0 + 1.0, 0.5))
    text(ctx, "（進んだ長さ）", (O[0] + P[0]) / 2 + 150, (O[1] + P[1]) / 2 + 80, 44, ORANGE, bold=False, alpha=a * fade(t, t0 + 1.0, 0.5))
    t_next = Sk("c1_p", 0.0)
    b = fade(t, t_next, 0.5)
    if b > 0.003:
        arrow_line(ctx, P[0], P[1], Q[0], Q[1], ORANGE, 9.0, 0.6 * b, 30.0)
        text(ctx, "足していく", (P[0] + Q[0]) / 2 + 20, (P[1] + Q[1]) / 2 - 55, 48, INK, alpha=b)


# ---- ch2: 歩測・矢印の図 ----
def L_foot2(ctx, t):
    t0 = Sk("c2_def", 0.0)
    a = fade(t, t0, 0.4)
    text(ctx, "歩いた数 × 歩幅 ＝ 距離", LCX, 140, 58, INK, alpha=a)
    walker(ctx, 690, 830, 360, a, step=t * 3.0)
    # 足あとの道（左下から旅人へ）
    path = np.array([[110 + 540 * k / 40, 895 - 70 * k / 40 - 12 * math.sin(k / 4.0)] for k in range(41)])
    footprints(ctx, path, int(40 * fade(t, t0 + 0.3, 1.8)) + 2, spacing=44.0, a=0.6 * a, size=14.0)
    text(ctx, "1歩ずつ 同じ幅で", 330, 760, 46, PENCIL_T, alpha=a * fade(t, t0 + 1.8, 0.4))


def L_arrow2(ctx, t):
    """道の前半は北へ。距離のぶれ→南北、向きのぶれ→東西"""
    t0 = Sk("c2_front", 0.0)
    a = fade(t, t0, 0.4)
    for (y0, y1) in ((70, 470), (500, 915)):
        ctx.set_source_rgba(1, 1, 1, 0.55 * a)
        rrect(ctx, 62, y0, 870, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * a))
        ctx.set_line_width(3)
        rrect(ctx, 62, y0, 870, y1 - y0, 16)
        ctx.stroke()
    # 上: 距離のぶれ → 南北
    ta = t0 + 0.4
    text(ctx, "距離のぶれ", 250, 112, 52, INK, alpha=a * fade(t, ta, 0.4))
    draw_poly(ctx, np.array([[230, 430], [230, 230]]), 7, NAVY, a)
    text(ctx, "北", 230, 196, 44, INK, alpha=a)
    arrow_line(ctx, 330, 430, 330, 190, ORANGE, 8, a * fade(t, ta + 0.5, 0.5), 28, both=True)
    text(ctx, "南北に出る", 640, 300, 60, RED, alpha=a * fade(t, ta + 1.2, 0.5))
    text(ctx, "進んだ長さが ちがう", 640, 380, 44, PENCIL_T, bold=False, alpha=a * fade(t, ta + 1.2, 0.5))
    # 下: 向きのぶれ → 東西
    tb = t0 + 2.6
    text(ctx, "向きのぶれ", 250, 548, 52, INK, alpha=a * fade(t, tb, 0.4))
    draw_poly(ctx, np.array([[230, 880], [230, 640]]), 7, NAVY, a)
    text(ctx, "北", 230, 610, 44, INK, alpha=a)
    draw_poly(ctx, np.array([[230, 880], [330, 640]]), 7, ORANGE, a * fade(t, tb + 0.5, 0.5))
    arrow_line(ctx, 244, 640, 322, 640, RED, 7, a * fade(t, tb + 1.0, 0.5), 24, both=True)
    text(ctx, "東西に出る", 640, 730, 60, RED, alpha=a * fade(t, tb + 1.2, 0.5))
    text(ctx, "進む向きが ちがう", 640, 810, 44, PENCIL_T, bold=False, alpha=a * fade(t, tb + 1.2, 0.5))


# ---- ch3: 杖先方位盤・距離と向きのずれの図 ----
def L_compass3(ctx, t):
    t0 = Sk("c3_stick", 0.0)
    a = fade(t, t0, 0.4)
    walker(ctx, 220, 905, 560, a, step=0.0)
    cx, cy, r = 650, 400, 190
    # 杖の先の方位盤（拡大）
    ctx.set_source_rgba(*hexrgb("#fff7e0", a))
    ctx.arc(cx, cy, r, 0, 6.2832)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(7)
    ctx.stroke()
    for k in range(72):
        ang = k * math.pi / 36
        ln = 26 if k % 6 == 0 else 13
        ctx.set_line_width(4 if k % 6 == 0 else 2.5)
        ctx.move_to(cx + (r - ln) * math.sin(ang), cy - (r - ln) * math.cos(ang))
        ctx.line_to(cx + (r - 4) * math.sin(ang), cy - (r - 4) * math.cos(ang))
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, a))                                       # 磁針（赤が北）
    ctx.move_to(cx, cy - r * 0.78)
    ctx.line_to(cx + 20, cy)
    ctx.line_to(cx - 20, cy)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#4a5a78", a))
    ctx.move_to(cx, cy + r * 0.78)
    ctx.line_to(cx + 20, cy)
    ctx.line_to(cx - 20, cy)
    ctx.close_path()
    ctx.fill()
    text(ctx, "杖先方位盤", 650, 128, 58, INK, alpha=a)
    text(ctx, "磁針", 650, 650, 52, RED, alpha=a * fade(t, t0 + 1.0, 0.4))
    # 杖の先から方位盤へ（拡大の線）
    staff_top = (220 + 0.20 * 560, 905 - 1.10 * 560)
    for sgn in (-1, 1):
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
        ctx.set_line_width(3)
        ctx.set_dash([10, 10])
        ctx.move_to(staff_top[0], staff_top[1] + sgn * 12)
        ctx.line_to(cx - r * 0.9, cy + sgn * r * 0.45)
        ctx.stroke()
        ctx.set_dash([])
    # 6分の1度の目もり（細かさ）
    b = fade(t, Sk("c3_6", 0.0), 0.4)
    if b > 0.003:
        ang0, ang1 = 0.0, math.radians(14)
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * b))
        ctx.set_line_width(8)
        ctx.arc(cx, cy, r - 40, -math.pi / 2, -math.pi / 2 + ang1)
        ctx.stroke()
        text(ctx, "細かい目もり", 650, 760, 52, INK, alpha=b)


def L_diag3(ctx, t):
    t0 = Sk("c3_dist", 0.0)
    a = fade(t, t0, 0.4)
    for (y0, y1) in ((70, 470), (500, 915)):
        ctx.set_source_rgba(1, 1, 1, 0.55 * a)
        rrect(ctx, 62, y0, 870, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * a))
        ctx.set_line_width(3)
        rrect(ctx, 62, y0, 870, y1 - y0, 16)
        ctx.stroke()
    text(ctx, "距離のずれ", LCX, 122, 56, INK, alpha=a)
    draw_poly(ctx, np.array([[130, 250], [600, 250]]), 8, NAVY, a)
    st = ease_in_out(clamp01((t - t0 - 0.5) / 1.2))
    st2 = 1.0 + 0.32 * math.sin(clamp01((t - t0 - 0.5) / 2.4) * 6.2832) * (1 if t > t0 + 0.5 else 0)
    draw_poly(ctx, np.array([[130, 330], [130 + 470 * (1 + 0.30 * st) * (st2 if t > t0 + 1.7 else 1.0), 330]]), 8, ORANGE, a * fade(t, t0 + 0.4, 0.4))
    text(ctx, "線が 伸び縮みする", LCX, 420, 50, RED, alpha=a * fade(t, t0 + 0.8, 0.5))
    t1 = Sk("c3_dir", 0.0)
    b = fade(t, t1, 0.4)
    text(ctx, "向きのずれ", LCX, 552, 56, INK, alpha=b)
    draw_poly(ctx, np.array([[150, 860], [840, 640]]), 8, NAVY, b)
    sw = ease_in_out(clamp01((t - t1 - 0.5) / 1.6))
    cu = np.array([[150 + 690 * k / 20, 860 - 220 * k / 20 + 105 * (k / 20) ** 2 * sw] for k in range(21)])
    draw_poly(ctx, cu, 8, ORANGE, b * fade(t, t1 + 0.4, 0.4))
    arrow_line(ctx, 842, 640, 842, 640 + 100 * sw + 1, RED, 6, b * sw, 22)
    text(ctx, "線が曲がって 横へ外れる", LCX - 40, 628, 50, RED, alpha=b * fade(t, t1 + 1.0, 0.5))


# ---- ch4: 緯度と星・象限儀 ----
def observer(ctx, cx, gy, el_deg, a, col_t, title, cap, h=200, title_dy=-395, cap_dy=62):
    ctx.set_source_rgba(*hexrgb("#e6dcc2", 0.9 * a))
    rrect(ctx, cx - 210, gy, 420, 22, 6)
    ctx.fill()
    draw_poly(ctx, np.array([[cx - 205, gy], [cx + 205, gy]]), 4, INK, a * 0.8)
    walker(ctx, cx - 60, gy, h, a, staff=False)
    head = (cx - 60, gy - 0.93 * h)
    el = math.radians(el_deg)
    sx, sy = head[0] + 190 * math.cos(el), head[1] - 190 * math.sin(el)
    dotted_line(ctx, head[0] + 18, head[1], sx, sy, PENCIL, 3.5, a * 0.9)
    star_shape(ctx, sx + 6, sy - 6, 30, "#ffd84d", a)
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.set_line_width(5)
    ctx.arc(head[0] + 18, head[1], 110, -el, 0)
    ctx.stroke()
    if title:
        text(ctx, title, cx, gy + title_dy, 46, col_t, alpha=a)
    text(ctx, cap, cx, gy + cap_dy, 44, RED, alpha=a)


def L_sky4(ctx, t):
    t0 = Sk("c4_lat", 0.0)
    a = fade(t, t0, 0.4)
    tt = Sk("c4_low", 0.0)
    b = fade(t, tt, 0.4)
    # 緯度＝南北の位置
    text(ctx, "緯度 ＝ 南北の位置", LCX, 110, 56, INK, alpha=a)
    arrow_line(ctx, 130, 260, 130, 170, INK, 6, a, 24)
    text(ctx, "北", 130, 140, 44, INK, alpha=a)
    observer(ctx, 250, 560, 58.0, b, RED, "", "南の町　星は高い")
    observer(ctx, 700, 560, 32.0, b * fade(t, tt + 0.7, 0.4), RED, "", "北の町　星は低い")
    # 象限儀
    tq = Sk("c4_quad", 0.0)
    c = fade(t, tq, 0.4)
    if c > 0.003:
        cx, cy, r = 190, 905, 235
        ctx.set_source_rgba(1, 0.97, 0.85, 0.9 * c)
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, -math.pi / 2, 0)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, c))
        ctx.set_line_width(6)
        ctx.stroke()
        for k in range(0, 91, 5):
            ang = math.radians(k)
            ln = 24 if k % 10 == 0 else 12
            ctx.set_line_width(3)
            ctx.move_to(cx + (r - ln) * math.cos(ang), cy - (r - ln) * math.sin(ang))
            ctx.line_to(cx + (r - 3) * math.cos(ang), cy - (r - 3) * math.sin(ang))
            ctx.stroke()
        el = math.radians(40)
        ex, ey = cx + 360 * math.cos(el), cy - 360 * math.sin(el)
        dotted_line(ctx, cx, cy, ex, ey, PENCIL, 3.5, c)
        star_shape(ctx, ex + 8, ey - 8, 28, "#ffd84d", c)
        draw_poly(ctx, np.array([[cx, cy], [cx + 3, cy - 180]]), 4, RED, c)
        text(ctx, "象限儀", 560, 770, 56, INK, alpha=c)
        text(ctx, "星の高さを測る", 600, 850, 46, PENCIL_T, alpha=c * fade(t, tq + 0.8, 0.4))


def L_map4(ctx, t):
    """星のところ（30kmごと）に印をつけ、描き直す（束が南北に動いて本当の線に吸いつく）"""
    paint_base(ctx)
    g0, g1 = S("g4"), E("g4")
    if t < g0:
        for i in range(12):
            draw_poly(ctx, PAIR_B[i], 3.4, ORANGE, 0.34)
    elif t < g1:
        bundle_grow_pair(ctx, t, g0, g1)
    else:
        for i in range(12):
            draw_poly(ctx, PAIR_A[i], 3.4, ORANGE, 0.34)
    # 星の印（30kmごと）。本当の道すじの上
    t30 = Sk("c4_30", 0.0)
    a = fade(t, t30, 0.5)
    if a > 0.003:
        idx = np.searchsorted(CUM[::3], np.arange(30.0, CUM[-1], 30.0))
        for j in idx:
            if j < len(TRUE_PX):
                star_shape(ctx, TRUE_PX[j][0], TRUE_PX[j][1], 10, "#ffd84d", a, 1.8)
    legend_map(ctx, 1.0)


# ---- ch5: 縄と鎖 ----
def L_rope5(ctx, t):
    t0 = Sk("c5_rope", 0.0)
    a = fade(t, t0, 0.4)
    # 縄（2本のより糸）
    text(ctx, "麻の縄", LCX, 130, 56, INK, alpha=a)
    xs = np.linspace(100, 880, 160)
    for sgn, col in ((1, "#b98f4f"), (-1, "#8a6a34")):
        pts = np.array([[x, 250 + sgn * 14 * math.sin((x - 100) / 22.0)] for x in xs])
        draw_poly(ctx, pts, 11, col, a * fade(t, t0 + 0.3, 0.6))
    for x in range(100, 881, 70):
        draw_poly(ctx, np.array([[x, 218], [x, 282]]), 4, INK, a * 0.8)
    t1 = Sk("c5_rope", 0.5) + 2.0
    b = fade(t, t1, 0.4)
    text(ctx, "鉄の輪をつないだ鎖", LCX, 480, 56, INK, alpha=b)
    for k in range(10):                                                          # 鎖の輪
        cxk = 140 + k * 76
        ctx.save()
        ctx.translate(cxk, 620)
        if k % 2:
            ctx.scale(0.55, 1.0)
        ctx.set_source_rgba(*hexrgb("#7d8aa3", b))
        ctx.set_line_width(13)
        rrect(ctx, -42, -26, 84, 52, 26)
        ctx.stroke()
        ctx.restore()
    for x in range(100, 881, 76):
        draw_poly(ctx, np.array([[x, 700], [x, 740]]), 4, INK, b * 0.8)
    text(ctx, "ぴんと張って 測る", LCX, 830, 48, PENCIL_T, alpha=b * fade(t, t1 + 0.8, 0.4))


# ---- ch6: 地球・星の間隔の小さな地図・伊能図との比較 ----
def L_earth6(ctx, t):
    t0 = Sk("c6_lat", 0.0)
    a = fade(t, t0, 0.4)
    cx, cy, r = LCX, 275, 175
    ctx.set_source_rgba(*hexrgb("#dbe9f5", 0.95 * a))
    ctx.arc(cx, cy, r, 0, 6.2832)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(6)
    ctx.stroke()
    ctx.save()
    ctx.translate(cx, cy)
    ctx.scale(1.0, 0.22)
    ctx.arc(0, 0, r, 0, 6.2832)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    ctx.stroke()
    text(ctx, "地球", cx, cy + r + 34, 44, INK, alpha=a)
    b = fade(t, Sk("c6_same", 0.0), 0.5)
    if b > 0.003:                                                                # 同じ緯度の線
        dy = -80
        rx = math.sqrt(r * r - dy * dy)
        ctx.save()
        ctx.translate(cx, cy + dy)
        ctx.scale(1.0, 0.22)
        ctx.arc(0, 0, rx, 0, 6.2832)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(RED, b))
        ctx.set_line_width(7)
        ctx.stroke()
        for sgn, nm in ((-1, "西"), (1, "東")):
            ctx.set_source_rgba(*hexrgb(RED, b))
            ctx.arc(cx + sgn * rx * 0.92, cy + dy + 6, 12, 0, 6.2832)
            ctx.fill()
            text(ctx, nm, cx + sgn * (rx * 0.92 + 52), cy + dy - 6, 52, RED, alpha=b)
        text(ctx, "同じ緯度の線", cx, 62, 46, RED, alpha=b)
    # 東の人・西の人（星の高さが同じ）
    c = fade(t, Sk("c6_same", 0.4), 0.5)
    if c > 0.003:
        for cxp, nm in ((250, "東にいる人"), (700, "西にいる人")):
            observer(ctx, cxp, 805, 45.0, c, INK, nm, "星の高さは 同じ", h=190, title_dy=48, cap_dy=96)


MAP4_BOX = [(55 + i * 222, 330, 205, 340) for i in range(4)]
COAST_KM = read_coast(34.4, 44.6, 138.0, 146.6)


def small_map_px(i):
    bx, by, bw, bh = MAP4_BOX[i]
    s = bh / (MY1 - MY0)

    def f(arr):
        a_ = np.asarray(arr, float)
        return np.stack([bx + (a_[:, 0] - MX0) * s, by + bh - (a_[:, 1] - MY0) * s], 1)
    return f


def L_maps4(ctx, t):
    t0 = Sk("c6_star", 0.0)
    a = fade(t, t0, 0.5)
    text(ctx, "星を見る回数を 変えてみた", LCX, 140, 52, INK, alpha=a)
    labs = ["多い", "", "", "少ない"]
    nstar = [16, 9, 4, 2]
    for i in range(4):
        bx, by, bw, bh = MAP4_BOX[i]
        ai = a * fade(t, t0 + 0.3 + 0.35 * i, 0.4)
        ctx.set_source_rgba(1, 1, 1, 0.6 * ai)
        rrect(ctx, bx - 4, by - 4, bw + 8, bh + 8, 10)
        ctx.fill()
        ctx.save()
        ctx.rectangle(bx - 4, by - 4, bw + 8, bh + 8)
        ctx.clip()
        f = small_map_px(i)
        for ln in COAST_KM:
            draw_poly(ctx, f(ln), 1.5, COAST_C, 0.5 * ai)
        draw_poly(ctx, f(TRUE[::3]), 3.5, NAVY, ai)
        for smp in RES["star_interval"][i]["samples"][:6]:
            draw_poly(ctx, f(np.array(smp)), 2.4, ORANGE, 0.55 * ai)
        tp = f(TRUE[::3])
        for j in np.linspace(8, len(tp) - 2, nstar[i]).astype(int):
            star_shape(ctx, tp[j][0], tp[j][1], 8, "#ffd84d", ai)
        ctx.restore()
        if labs[i]:
            text(ctx, labs[i], bx + bw / 2, by + bh + 44, 46, INK, alpha=ai)
    arrow_line(ctx, 130, 790, 840, 790, INK, 6, a * fade(t, t0 + 1.8, 0.5), 22)
    text(ctx, "星を見る回数", LCX, 860, 46, PENCIL_T, alpha=a * fade(t, t0 + 1.8, 0.5))
    ts = Sk("c6_star", 0.55)
    text(ctx, "ずれは ほとんど変わらない", LCX, 240, 48, RED, alpha=a * fade(t, ts, 0.5))


# ---- 伊能図 ----
INO_SC = 0.265
_INO_SURF = {}


def ino_surface(key):
    if key not in _INO_SURF:
        from PIL import Image
        im = Image.open(INO_FILES[key]).convert("RGBA")
        w, h = int(im.width * INO_SC), int(im.height * INO_SC)
        arr = np.array(im.resize((w, h), Image.LANCZOS))
        bgra = bytearray(arr[..., [2, 1, 0, 3]].tobytes())
        _INO_SURF[key] = (cairo.ImageSurface.create_for_data(bgra, cairo.FORMAT_ARGB32, w, h, w * 4), bgra, w, h)
    return _INO_SURF[key]


_INO_FRAME = {}


def ino_frame(key):
    """画像の中心の緯度経度と、左の今の地図の 1km あたりの画素（画像と同じ縮尺）"""
    if key not in _INO_FRAME:
        sh = INO["sheets"][key]
        m = InoMap(sh["grid"])
        W, H = sh["grid"]["size"]
        lat_c, lon_c = m.px_to_ll(W / 2, H / 2)
        ys = sorted([(int(k), v["co"][0] + v["co"][1] * W / 2) for k, v in sh["grid"]["hl"].items()])
        spacing = (ys[0][1] - ys[-1][1]) / (ys[-1][0] - ys[0][0])          # 緯度1度あたりの画素（画像の画素）
        kmpx = spacing * INO_SC / 111.19
        _INO_FRAME[key] = (m, lat_c, lon_c, kmpx)
    return _INO_FRAME[key]


NAMES_ISLAND = {"屋久島の西はし": "屋久島", "屋久島の東はし": None, "種子島の北はし": "種子島", "種子島の南はし": None}
LABEL_POS = {"納沙布岬": ("r", -24, -50), "襟裳岬": ("r", -10, 50), "知床岬": ("r", -14, -50), "佐多岬": ("l", 0, 8), "屋久島の西はし": ("r", 0, 58), "種子島の北はし": ("r", 70, -12)}
ARROW_LABEL = {"hokkaido": ("納沙布岬", 52), "kyushu": ("佐多岬", -52)}        # 「伊能図ではここ」の札をつける矢印（1シートに1つ）
CAPTION_INO = {"hokkaido": "日本沿海輿地図（中図）北海道東部", "kyushu": "日本沿海輿地図（中図）九州南部"}
CAPTION_INO2 = "東京国立博物館所蔵　出典: ColBase"
LAT_RANGE = {"hokkaido": (41, 42, 43, 44, 45), "kyushu": (30, 31, 32)}
COAST_LL = {"hokkaido": read_coast_ll(41.0, 45.8, 142.0, 148.6), "kyushu": read_coast_ll(29.3, 33.6, 128.4, 132.6)}


_CMP = {}


def cmp_geo(key):
    """左の今の地図・右の伊能図の置き場所と、描くものの画面の位置（一度だけ計算して覚える）"""
    if key not in _CMP:
        sh = INO["sheets"][key]
        surf, _buf, w, h = ino_surface(key)
        m, lat_c, lon_c, kmpx = ino_frame(key)
        x0, y0 = int(RCX_PAGE - w / 2), 36
        lx0 = int(LCX + 35 - w / 2)                                  # 左の地図の「伊能図の左はし」の位置。左の枠は西へ70画素ひろげて（岬が枠の外に出ないように）同じ縮尺で描く

        def L2P(lat, lon):
            return (lx0 + w / 2 + (lon - lon_c) * 111.19 * math.cos(math.radians(lat_c)) * kmpx, y0 + h / 2 - (lat - lat_c) * 111.19 * kmpx)
        g = dict(sh=sh, surf=surf, w=w, h=h, x0=x0, y0=y0, lx0=lx0, L2P=L2P, fx0=lx0 - 70, fw=w + 70)
        g["coast"] = [np.array([L2P(la, lo) for lo, la in thin(ln, 0.004)]) for ln in COAST_LL[key]]
        g["lat"] = [(lat, L2P(lat, lon_c)[1]) for lat in range(25, 50) if y0 < L2P(lat, lon_c)[1] < y0 + h]
        g["lon"] = [L2P(lat_c, lon)[0] for lon in range(125, 150) if lx0 - 70 < L2P(lat_c, lon)[0] < lx0 + w]
        _CMP[key] = g
    return _CMP[key]


def L_compare(ctx, t, key, ta):
    """左＝今の地図（地球地図日本の海岸線・北が上・伊能図と同じ範囲と縮尺）、右＝伊能図の画像。矢印は ta 秒から"""
    g = cmp_geo(key)
    sh, surf, w, h, x0, y0, lx0, L2P = g["sh"], g["surf"], g["w"], g["h"], g["x0"], g["y0"], g["lx0"], g["L2P"]
    # ---- 右: 伊能図 ----
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.25)
    rrect(ctx, x0 + 6, y0 + 8, w, h, 4)
    ctx.fill()
    ctx.set_source_surface(surf, x0, y0)
    ctx.paint()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3)
    ctx.rectangle(x0, y0, w, h)
    ctx.stroke()
    # ---- 左: 今の地図 ----
    fx0, fw = g["fx0"], g["fw"]
    ctx.set_source_rgba(1, 1, 1, 0.6)
    ctx.rectangle(fx0, y0, fw, h)
    ctx.fill()
    ctx.save()
    ctx.rectangle(fx0, y0, fw, h)
    ctx.clip()
    for lat, yy in g["lat"]:                                              # 緯線・経線（1度ごと）
        draw_poly(ctx, np.array([[fx0, yy], [fx0 + fw, yy]]), 2.0, "#9db4cf", 0.9)
    for xx in g["lon"]:
        draw_poly(ctx, np.array([[xx, y0], [xx, y0 + h]]), 2.0, "#9db4cf", 0.9)
    for pts in g["coast"]:
        draw_poly(ctx, pts, 3.0, NAVY, 0.95)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3)
    ctx.rectangle(fx0, y0, fw, h)
    ctx.stroke()
    for lat, yy in g["lat"]:
        if y0 + 30 < yy < y0 + h - 10:
            text(ctx, f"北緯{lat}度", fx0 + 10, yy - 22, 40, "#3a5b8a", align="left", alpha=1.0)
    # 点（今の位置の○・名前）。今の地図の側だけに、東にずれている点から「伊能図ではここ」へ向かう太い矢印（向きと長さは実測のまま）
    u = ease_in_out(clamp01((t - ta) / 0.9))
    for p in sh["points"]:
        q = L2P(*p["modern"])
        ctx.set_source_rgba(1, 1, 1, 0.5)
        ctx.arc(q[0], q[1], 11, 0, 6.2832)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(RED, 1.0))
        ctx.set_line_width(5)
        ctx.arc(q[0], q[1], 11, 0, 6.2832)
        ctx.stroke()
        nm = NAMES_ISLAND.get(p["name"], p["name"])
        if nm and p["name"] in LABEL_POS:
            side, dx, dy = LABEL_POS[p["name"]]
            xl = q[0] + dx if side == "r" else q[0] - 24 - text_width(nm, 40) - 26 + dx
            tag(ctx, nm, xl, q[1] + dy, 40, INK, 1.0, align="left")
    if u > 0.003:
        for p in sh["points"]:
            if not p["east"]:
                continue
            A = L2P(*p["modern"])
            B = L2P(*p["ino_ll"])
            E_ = (A[0] + (B[0] - A[0]) * u, A[1] + (B[1] - A[1]) * u)
            ang = math.atan2(E_[1] - A[1], E_[0] - A[0])
            s0 = (A[0] + 8 * math.cos(ang), A[1] + 8 * math.sin(ang))
            if math.hypot(E_[0] - s0[0], E_[1] - s0[1]) > 10:
                arrow_line(ctx, s0[0], s0[1], E_[0], E_[1], RED, 10.0, 1.0, max(18.0, min(32.0, 0.6 * math.hypot(E_[0] - s0[0], E_[1] - s0[1]))))
            if PEOPLE_ON[0] and u > 0.99:
                ARROW_LOG.append((key, A[0], A[1], B[0], B[1]))
            if p["name"] == ARROW_LABEL[key][0] and u > 0.6:
                tag(ctx, "伊能図ではここ", min(max(B[0] - 10, fx0 + 8), fx0 + fw - 312), B[1] + ARROW_LABEL[key][1], 40, RED, fade(t, ta + 0.5, 0.3), align="left")
    # 右: 伊能図の実画像。赤い線・矢印は載せない。対応する点（伊能図での位置）に小さな○だけ
    if u > 0.003:
        for p in sh["points"]:
            ix, iy = p["ino_px"]
            ctx.set_source_rgba(1, 1, 1, 0.5 * u)
            ctx.arc(x0 + ix * INO_SC, y0 + iy * INO_SC, 8, 0, 6.2832)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(RED, u))
            ctx.set_line_width(4)
            ctx.arc(x0 + ix * INO_SC, y0 + iy * INO_SC, 8, 0, 6.2832)
            ctx.stroke()
    # キャプション
    text(ctx, "今の地図（北が上）", LCX, 864, 40, INK, alpha=1.0)
    text(ctx, "赤い○＝今の位置　矢印の先＝伊能図の位置", LCX, 903, 40, RED, alpha=1.0)
    text(ctx, CAPTION_INO[key], RCX_PAGE, 864, 40, INK, alpha=1.0)
    text(ctx, CAPTION_INO2, RCX_PAGE, 903, 40, INK, alpha=1.0)


RCX_PAGE = 1425


# ---- ch7: 地球・1度・2つの山 ----
def L_earth7(ctx, t):
    t0 = Sk("c7_def", 0.0)
    a = fade(t, t0, 0.4)
    cx, cy, r = LCX, 330, 235
    ctx.set_source_rgba(*hexrgb("#dbe9f5", 0.95 * a))
    ctx.arc(cx, cy, r, 0, 6.2832)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(6)
    ctx.stroke()
    a1, a2 = math.radians(-82), math.radians(-66)                                  # 中心から2本の半径（広げて描く）
    for an in (a1, a2):
        draw_poly(ctx, np.array([[cx, cy], [cx + r * math.cos(an), cy + r * math.sin(an)]]), 5, INK, a)
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.set_line_width(12)
    ctx.arc(cx, cy, r, a1, a2)
    ctx.stroke()
    ctx.set_line_width(5)
    ctx.arc(cx, cy, 90, a1, a2)
    ctx.stroke()
    text(ctx, "緯度1度", cx + 120, cy - 190, 52, RED, alpha=a * fade(t, t0 + 0.6, 0.4))
    text(ctx, "地球の中心", cx, cy + 40, 40, PENCIL_T, alpha=a)
    b = fade(t, Sk("c7_def", 0.55), 0.5)
    text(ctx, "この長さ × 360 ＝ 地球1周", LCX, 640, 54, INK, alpha=b)
    c = fade(t, Sk("c7_def", 0.8), 0.5)
    text(ctx, "距離 ÷ 緯度の差 ＝ 1度の長さ", LCX, 735, 52, INK, alpha=c)
    text(ctx, "江戸から北へ 約600km", LCX, 820, 52, ORANGE, alpha=c * fade(t, Sk("c7_def", 0.9), 0.4))


HIST_X = (110.0, 880.0)                                                            # 山の図の横軸（画面）
HIST_RANGE = (108.5, 113.5)


def hx(v):
    return HIST_X[0] + (v - HIST_RANGE[0]) / (HIST_RANGE[1] - HIST_RANGE[0]) * (HIST_X[1] - HIST_X[0])


def L_hist7(ctx, t):
    """縄・鎖と磁石で測った1万回の「1度の長さ」の山（data.json の度数）と、点線＝この球の1度"""
    t0 = Sk("c7_b2", 0.0)
    a = fade(t, t0, 0.4)
    base_y = 740
    text(ctx, "1万回の 1度の長さ（km）", LCX, 130, 56, INK, alpha=a)
    h_ = np.array(RES["degree"][1]["hist"], float)
    mx = h_.max()
    nb = len(h_)
    lo, hi = RES["degree"][1]["edges"]
    grow = ease_out(clamp01((t - t0 - 0.3) / 3.0))
    pts = [(hx(max(lo, HIST_RANGE[0])), base_y)]
    for k in range(nb):
        v0 = lo + (hi - lo) * k / nb
        v1 = lo + (hi - lo) * (k + 1) / nb
        if v1 < HIST_RANGE[0] or v0 > HIST_RANGE[1]:
            continue
        hh = h_[k] / mx * 460 * grow
        pts += [(hx(max(v0, HIST_RANGE[0])), base_y - hh), (hx(min(v1, HIST_RANGE[1])), base_y - hh)]
    pts.append((hx(HIST_RANGE[1]), base_y))
    ctx.set_source_rgba(*hexrgb(BLUE, 0.42 * a))
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(BLUE, a))
    ctx.set_line_width(4)
    ctx.stroke()
    draw_poly(ctx, np.array([[hx(HIST_RANGE[0]), base_y], [hx(HIST_RANGE[1]), base_y]]), 4, INK, a)
    for v in (109, 110, 111, 112, 113):
        text(ctx, str(v), hx(v), base_y + 38, 40, INK, alpha=a)
    xs = hx(RES["true_deg"])
    dotted_line(ctx, xs, base_y + 6, xs, 215, RED, 6, a * fade(t, Sk("c7_b2", 0.55), 0.5))
    tag(ctx, "この球の1度", xs - 215, 190, 40, RED, a * fade(t, Sk("c7_b2", 0.55), 0.5), align="left")
    al = a * fade(t, t0 + 1.0, 0.4)
    ctx.set_source_rgba(*hexrgb(BLUE, 0.8 * al))
    ctx.rectangle(110, 866 - 16, 32, 32)
    ctx.fill()
    text(ctx, "縄・鎖＋磁石の向き", 160, 866, 44, BLUE, align="left", alpha=al)
    text(ctx, "江戸から北へ 約600km 測る", 110, 910, 44, ORANGE, align="left", alpha=al)


def L_end8(ctx, t):
    """まとめ: 地図は出さない（本当の形と重なって見えにくいため）。左ページは大きな数字だけ（右の5本の棒と同じ値）"""
    a = fade(t, Sk("c8_1", 0.15), 0.5)
    text(ctx, "ずれ（真ん中の回）", LCX, 230, 56, INK, alpha=a)
    text(ctx, f"約{ihalf(VAL['L0'])}km", LCX, 400, 120, RED, alpha=a)
    arrow_line(ctx, LCX, 480, LCX, 580, INK, 9, a * fade(t, Sk("c8_1", 0.5), 0.5), 36)
    text(ctx, f"{VAL['L4']:.1f}km", LCX, 710, 120, ORANGE, alpha=a * fade(t, Sk("c8_1", 0.6), 0.5))


# ============================================================
# 層の時刻表（左ページ）
# ============================================================
LAYERS = []


def layer(name, t0, t1, fn, fi=0.4, fo=0.4):
    LAYERS.append((name, t0, t1, fn, fi, fo))


T_ES = Ek("c8_end") + 0.3          # 終了画面の始まり（まとめの最後の説明を言い終わって 0.3秒後）
T_CMP = Sk("c6_look", 0.0)
T_CMP2 = Sk("c6_kyu", 0.0)                                         # 「九州は、参考として…」のところで九州南部の比べる絵に切りかえる
layer("title", 0.0, S("ch1") + 0.3, lambda ctx, t: L_title(ctx, t), fi=0.0)
layer("ch0", 0.0, S("ch1"), L_ch0, fi=0.0)
layer("walk_big", Sk("c0_ino", -0.1), Sk("c0_n", 0.0) + 2.0, L_walk_big)
layer("map1a", S("ch1"), Sk("c1_m"), lambda ctx, t: L_map(ctx, t, "L0", bundle=False))
layer("seg1", Sk("c1_m"), S("g1"), L_seg1)
layer("map1b", S("g1"), S("ch2"), lambda ctx, t: L_map(ctx, t, "L0", grow=(S("g1"), E("g1")), med=(t > Sk("c1_r", 0.0))))
layer("map2a", S("ch2"), Sk("c2_def"), lambda ctx, t: L_map(ctx, t, "L0", bundle=False))
layer("foot2", Sk("c2_def"), S("g2"), L_foot2)
layer("map2b", S("g2"), Sk("c2_front"), lambda ctx, t: L_map(ctx, t, "L1", grow=(S("g2"), E("g2")), med=(t > Sk("c2_r", 0.0))))
layer("arrow2", Sk("c2_front"), S("ch3"), L_arrow2)
layer("map3a", S("ch3"), Sk("c3_stick"), lambda ctx, t: L_map(ctx, t, "L1", bundle=True))
layer("compass3", Sk("c3_stick"), S("g3"), L_compass3)
layer("map3b", S("g3"), Sk("c3_dist"), lambda ctx, t: L_map(ctx, t, "L2", grow=(S("g3"), E("g3")), med=(t > Sk("c3_r", 0.0))))
layer("diag3", Sk("c3_dist"), Sk("c3_km25"), L_diag3)
layer("map3c", Sk("c3_km25"), S("ch4"), lambda ctx, t: L_map(ctx, t, "L2", med=True))
layer("map4a", S("ch4"), Sk("c4_lat"), lambda ctx, t: L_map(ctx, t, "L2", med=True))
layer("sky4", Sk("c4_lat"), Sk("c4_09"), L_sky4)
layer("map4b", Sk("c4_09"), S("ch5"), L_map4)
layer("map5a", S("ch5"), Sk("c5_rope"), lambda ctx, t: L_map(ctx, t, "L3", med=True))
layer("rope5", Sk("c5_rope"), S("g5"), L_rope5)
layer("map5b", S("g5"), S("ch6"), lambda ctx, t: L_map(ctx, t, "L4", grow=(S("g5"), E("g5")), med=(t > Sk("c5_r", 0.0))))
layer("earth6", S("ch6"), T_CMP, L_earth6)
layer("cmpH", T_CMP, T_CMP2, lambda ctx, t: L_compare(ctx, t, "hokkaido", Sk("c6_east", 0.0) + 0.3))
layer("cmpK", T_CMP2, S("ch7"), lambda ctx, t: L_compare(ctx, t, "kyushu", T_CMP2 + 0.3))
layer("earth7", S("ch7"), Sk("c7_b2"), L_earth7)
layer("hist7", Sk("c7_b2"), S("ch8"), L_hist7)
layer("end8", S("ch8"), T_ES + 0.8, L_end8)


LAYER_OUT, LAYER_IN, LAYER_DELAY = 0.2, 0.25, 0.2


def draw_left(ctx, t):
    for name, t0, t1, fn, fi, fo in LAYERS:
        fo = min(fo, LAYER_OUT)
        if t < t0 - 1e-6 or t > t1 + fo:
            continue
        a_in = 1.0 if fi <= 0 else ease_out(clamp01((t - t0 - LAYER_DELAY) / LAYER_IN))
        a = a_in * (1.0 if fo <= 0 else 1 - clamp01((t - t1) / fo))
        ctx.save()
        if not name.startswith("cmp"):                  # 伊能図の比べる絵だけは、右ページにもまたがって描く
            clip_left(ctx)
        grp(ctx, a, fn, t)
        ctx.restore()


# ---- 左の細い帯の札（地図の左）。台本の文から出て、章の終わり（または次の絵）で消える ----
def _tags_def():
    return [
        # (手がかり, 文字, y, 色, 出る時刻の割合, 消える時刻)
        ("c1_r", "ずれ 約50km", 330, RED, 0.5, S("ch2")), ("c1_ew", "東西 21.7km", 410, INK, 0.2, S("ch2")), ("c1_ns", "南北 36.7km", 490, INK, 0.2, S("ch2")),
        ("c2_r", "ずれ 24.4km", 330, RED, 0.5, Sk("c2_front")),
        ("c2_ns", "東西", 410, INK, 0.3, Sk("c2_n2")), ("c2_ns", "南北", 490, INK, 0.3, Sk("c2_n2")),
        ("c2_n2", "東西 19.1km", 410, INK, 0.7, Sk("c2_front")), ("c2_n2", "南北 10.0km", 490, INK, 0.0, Sk("c2_front")),
        ("c3_r", "ずれ 8.3km", 330, RED, 0.5, Sk("c3_dist")), ("c3_km25", "ずれ 8.3km", 330, RED, 0.0, S("ch4")),
        ("c3_ew", "東西 2.9km", 410, INK, 0.0, S("ch4")), ("c3_ns", "南北 7.3km", 490, INK, 0.1, S("ch4")),
        ("c4_r", "ずれ 3.1km", 330, RED, 0.5, S("ch5")),
        ("c4_ns", "南北 7.3km", 410, INK, 0.0, Sk("c4_ns", 0.55)), ("c4_ns", "南北 0.7km", 410, INK, 0.55, S("ch5")),
        ("c4_ew", "東西 2.9km", 490, INK, 0.2, S("ch5")),
        ("c5_r", "ずれ 2.2km", 330, RED, 0.5, S("ch6")), ("c5_ew", "東西 1.9km", 410, INK, 0.3, S("ch6")),
    ]


TAGS = _tags_def()


def draw_strip_tags(ctx, t):
    ctx.save()
    clip_left(ctx)
    for key, s_, y, col, fr, until in TAGS:
        t0 = Sk(key, fr)
        if t < t0 or t > until + 0.4:
            continue
        a = fade(t, t0 + 0.4, 0.25) * out_fade(t, until, 0.3)
        tag(ctx, s_, SX, y, 52, col, a, align="left")
    ctx.restore()


# ============================================================
# 右ページ（付せん・ずれの棒の枠）
# ============================================================
def stk(ctx, t, key, s, y, color="yellow", fg=INK, a=1.0, size=40, tilt=-0.012, off=0.3, x=RX, frac=0.0):
    """右ページの付せん。台本の文（手がかり key）から現れる"""
    t0 = Sk(key, frac) + off
    if t >= t0:
        return mini_sticky(ctx, s, x, y, size, color, fg=fg, a=a * fade(t, t0), align="left", tilt=tilt)
    return 0, 0


QLINES = ["歩いて測った", "日本地図は、", "どこまで", "正確になる？"]
QTXT = "\n".join(QLINES)                                 # 題名と同じ言葉（最初は 92px・4行。「伊能忠敬は」の文の途中で小さく2行にして、付せんの場所をあける）
QSMALL = "歩いて測った日本地図は、\nどこまで正確になる？"
Q_BIG = 92
T_Q_SHRINK = Sk("c0_ino", 0.35)
N_COUNT_END = 3.2                                        # 冒頭の「ずれ」の数を伏せる時刻


def counter_val(t):
    """冒頭の「ずれ」の数（km）: 歩く点と本当の道すじの、そのときの距離（見本1回ぶん）"""
    u = clamp01(t / T_WALK)
    i = int(u * (len(OPEN_DEV) - 1))
    return OPEN_DEV[i]


def R_ch0(ctx, t):
    big = out_fade(t, T_Q_SHRINK - 0.2, 0.2)
    if big > 0.003:
        text(ctx, QTXT, RX, 318, Q_BIG, INK, align="left", alpha=big)
        pen_line(ctx, RX - 4, 548, RX + text_width("正確になる？", Q_BIG) + 4, 544, RED, seed=5, width=9, progress=clamp01(t / 0.6), alpha=big)
    small = fade(t, T_Q_SHRINK + 0.05, 0.2)
    if small > 0.003:
        text(ctx, QSMALL, RX, 170, 64, INK, align="left", alpha=small)
        pen_line(ctx, RX - 4, 250, RX + text_width("どこまで正確になる？", 64) + 4, 246, RED, seed=5, width=7, alpha=small)
    if t >= Sk("c0_n", 0.3):
        sticky(ctx, "1万回", RX + 135, 340, 64, "pink", fg=RED, a=fade(t, Sk("c0_n", 0.3), 0.3), tilt=-0.02)
    if t >= Sk("c0_z", 0.45):
        mini_sticky(ctx, "ずれ", RX + 390, 340, 64, "yellow", fg=RED, a=fade(t, Sk("c0_z", 0.45), 0.3), align="left", tilt=0.015)


def R_ch1(ctx, t):
    stk(ctx, t, "c1_o", "出発点", 150, "yellow", size=56, tilt=-0.015)
    w1, _ = stk(ctx, t, "c1_p", "距離 150m", 250, "pink", fg=RED, size=52, tilt=-0.012, off=0.2)
    if t >= Sk("c1_p", 0.45):
        mini_sticky(ctx, "方位 8度", RX + w1 + 24, 250, 52, "pink", fg=RED, a=fade(t, Sk("c1_p", 0.45), 0.3), align="left", tilt=0.012)
    stk(ctx, t, "c1_p", "ぶれの大きさはこの動画の置き方", 345, "mint", size=40, tilt=-0.008, off=1.2)


def R_ch2(ctx, t):
    stk(ctx, t, "c2_69", "約69cm（推定）", 150, "yellow", size=52, tilt=-0.012, off=0.2)
    stk(ctx, t, "c2_50", "距離 50m", 250, "pink", fg=RED, size=52, tilt=0.012, off=0.2)
    stk(ctx, t, "c2_half", "ほぼ半分", 350, "mint", size=52, tilt=-0.01, off=0.2)


def R_ch3(ctx, t):
    stk(ctx, t, "c3_6", "6分の1度まで読める", 140, "yellow", size=44, off=0.2)
    stk(ctx, t, "c3_03", "方位 0.3度", 235, "pink", fg=RED, size=52, tilt=0.012, off=0.2)
    stk(ctx, t, "c3_km25", "歩幅 約25km減", 330, "mint", size=42, off=0.2)
    stk(ctx, t, "c3_km16", "磁石 約16km減", 410, "mint", size=42, tilt=0.01, off=0.2)
    stk(ctx, t, "c3_ratio", "割合では向きが効いた", 495, "pink", fg=RED, size=42, off=0.4)


def R_ch4(ctx, t):
    stk(ctx, t, "c4_lat", "緯度 ＝ 南北の位置", 140, "mint", size=44, off=0.3)
    stk(ctx, t, "c4_09", "星のぶれ 0.9km", 235, "pink", fg=RED, size=48, tilt=0.012, off=0.3, frac=0.5)
    stk(ctx, t, "c4_30", "30kmごとに星", 330, "yellow", size=48, off=0.2)
    stk(ctx, t, "c4_redraw", "東西は そのまま", 425, "blue", size=44, off=0.3, tilt=-0.01)


def R_ch5(ctx, t):
    w1, _ = stk(ctx, t, "c5_rope", "間縄", 150, "yellow", size=56, tilt=-0.015, off=0.2)
    if t >= Sk("c5_rope", 0.5):
        mini_sticky(ctx, "鉄鎖", RX + w1 + 30, 150, 56, "blue", fg=INK, a=fade(t, Sk("c5_rope", 0.5), 0.3), align="left", tilt=0.012)
    stk(ctx, t, "c5_if", "もし縄・鎖なら", 255, "mint", size=52, off=0.3)
    stk(ctx, t, "c5_10", "距離 10m", 360, "pink", fg=RED, size=52, tilt=0.012, off=0.2)


def R_ch6(ctx, t):
    a = out_fade(t, T_CMP - 0.1, 0.4)
    if a <= 0.003:
        return
    grp(ctx, a, _R_ch6_body, t)


def _R_ch6_body(ctx, t):
    stk(ctx, t, "c6_time", "時刻が 江戸と違う", 150, "yellow", size=44, off=0.3)
    stk(ctx, t, "c6_clock", "持ち運べる時計 なし", 245, "pink", fg=RED, size=44, tilt=0.01, off=0.3)
    stk(ctx, t, "c6_then", "東西は 足していくだけ", 340, "mint", size=44, off=0.3)


def R_ch7(ctx, t):
    stk(ctx, t, "c7_def", "緯度1度の長さ", 150, "yellow", size=52, tilt=-0.012, off=0.2)


R_CH = [R_ch0, R_ch1, R_ch2, R_ch3, R_ch4, R_ch5, R_ch6, R_ch7]


def draw_right(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    if idx >= len(R_CH):
        return
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, R_CH[idx - 1], t)
    R_CH[idx](ctx, t)


# ---- ずれの棒の枠（右下。ch1 から答えの文で伸びる。ch8 で右ページいっぱいに並べる）----
GEO_PS = dict(box=(1030, 560, 1830, 920), cap=(1062, 594, 44), label_x=1062, label_size=44, track_x=1300, track_w=250, val_x=1566,
              val_size=48, bar_h=34, rows=[656, 716, 776, 836, 896])
GEO_PB = dict(box=(1030, 100, 1830, 920), cap=(1062, 150, 46), label_x=1062, label_size=56, track_x=1370, track_w=260, val_x=1646,
              val_size=60, bar_h=52, rows=[290, 420, 550, 680, 810])
LABELS = ["目分量", "＋歩幅", "＋磁石", "＋星", "＋縄・鎖"]
VTXT = ["約50", f"{VAL['L1']:.1f}", f"{VAL['L2']:.1f}", f"{VAL['L3']:.1f}", f"{VAL['L4']:.1f}"]
VMAX = 50.0                                                  # 棒の枠の幅 ＝ 50km
LADDER_ROWS = [  # (行, 名札, id, 名札の時刻, 棒の時刻, 色)
    (0, "目分量", "L0", lambda: S("ch1") + 0.9, lambda: Sk("c1_r", 0.6), RED),
    (1, "＋歩幅", "L1", lambda: S("ch2") + 0.9, lambda: Sk("c2_r", 0.5), ORANGE),
    (2, "＋磁石", "L2", lambda: S("ch3") + 0.9, lambda: Sk("c3_r", 0.5), ORANGE),
    (3, "＋星", "L3", lambda: S("ch4") + 0.9, lambda: Sk("c4_r", 0.5), ORANGE),
    (4, "＋縄・鎖", "L4", lambda: S("ch5") + 0.9, lambda: Sk("c5_r", 0.5), ORANGE),
]


def bar_row(ctx, G, i, label, la, col, frac, vtxt, bu, ta, vsz=None, lcol=INK):
    """1本の棒。la=名札の濃さ、ta=枠の濃さ、bu=棒の伸び（0〜1）"""
    y = G["rows"][i]
    tx, tw, bh = G["track_x"], G["track_w"], G["bar_h"]
    if ta > 0.003:
        ctx.set_source_rgba(1, 1, 1, 0.7 * ta)
        rrect(ctx, tx, y - bh / 2, tw, bh, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * ta))
        ctx.set_line_width(2.5)
        rrect(ctx, tx, y - bh / 2, tw, bh, 6)
        ctx.stroke()
    if la > 0.003 and label:
        text(ctx, label, G["label_x"], y, G["label_size"], lcol, align="left", alpha=la)
    if bu > 0.003 and ta > 0.003:
        wd = max(4.0, tw * frac) * bu if frac > 0 else 0.0
        if wd > 0:
            ctx.set_source_rgba(*hexrgb(col, 0.92 * ta))
            rrect(ctx, tx, y - bh / 2, wd, bh, 6)
            ctx.fill()
        if vtxt and bu > 0.15:
            text(ctx, vtxt, G["val_x"], y, vsz or G["val_size"], col, align="left", alpha=ta * clamp01((bu - 0.15) / 0.3))


def draw_box(ctx, G, a, y1=None):
    x0, y0, x1, y1_ = G["box"]
    y1 = y1_ if y1 is None else y1
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()


def bu_of(t, tb, d=0.9):
    return ease_out(clamp01((t - tb) / d))


def panel_small(ctx, t, a):
    G = GEO_PS
    t_fr = Sk("c0_i", 0.3)                                               # 「ずれの棒が5本並ぶ枠」が出る
    draw_box(ctx, G, a, lerp(712.0, G["box"][3], ease_out(clamp01((t - t_fr + 0.1) / 0.6))))      # 最初は1行ぶん。枠が出るときに5本ぶんへ広がる
    tz_a = out_fade(t, t_fr, 0.2)
    if tz_a > 0.003:                                                     # ch0 の「ずれ」の数（歩く点の見本）。3.2秒で伏せて「？」にする
        ya = 640
        text(ctx, "ずれ", 1062, ya, 64, RED, align="left", alpha=a * tz_a)
        if t < N_COUNT_END:
            v = ihalf(counter_val(t))
            text(ctx, f"{v}", 1560, ya, 84, RED, align="right", alpha=a * tz_a * fade(t, 0.15, 0.3))
        else:
            text(ctx, "？", 1560, ya, 84, RED, align="right", alpha=a * tz_a * fade(t, N_COUNT_END, 0.3))
        text(ctx, "km", 1580, ya + 6, 48, RED, align="left", alpha=a * tz_a * fade(t, 0.15, 0.3))
    cap = fade(t, t_fr + 0.25, 0.3) * a
    text(ctx, "ずれ（km・真ん中の回）", G["cap"][0], G["cap"][1], G["cap"][2], INK, align="left", alpha=cap)
    for (i, lab, vid, tlf, tbf, col) in LADDER_ROWS:
        ta = a * fade(t, t_fr + 0.12 * (i + 1), 0.4)
        bar_row(ctx, G, i, lab, fade(t, tlf(), 0.4) * a, col, VAL[vid] / VMAX, VTXT[i], bu_of(t, tbf()), ta)


def panel_big(ctx, t, a):
    """ch8: ずれの棒を5本並べる（約50 → 24.4 → 8.3 → 3.1 → 2.2 km）"""
    G = GEO_PB
    draw_box(ctx, G, a)
    text(ctx, "ずれ（km・真ん中の回）", G["cap"][0], G["cap"][1], G["cap"][2], INK, align="left", alpha=a)
    for j, (i, lab, vid, _tl, _tb, col) in enumerate(LADDER_ROWS):
        tb = Sk("c8_1", 0.1) + 0.9 * j
        bar_row(ctx, G, j, lab, a * fade(t, tb - 0.2, 0.4), col, VAL[vid] / VMAX, VTXT[j], bu_of(t, tb), a * fade(t, tb - 0.2, 0.4))
    for j in range(4):                                                   # 矢印（約50 → 24.4 → 8.3 → 3.1 → 2.2）
        y = (G["rows"][j] + G["rows"][j + 1]) / 2
        ar = a * fade(t, Sk("c8_1", 0.1) + 0.9 * (j + 1) - 0.3, 0.4)
        if ar > 0.003:
            xx = G["track_x"] + 40
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.85 * ar))
            ctx.set_line_width(5)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(xx, y - 22)
            ctx.line_to(xx, y + 22)
            ctx.stroke()
            ctx.move_to(xx - 10, y + 10)
            ctx.line_to(xx, y + 24)
            ctx.line_to(xx + 10, y + 10)
            ctx.stroke()


# ---- ch7: 緯度1度の長さの棒（4本）と、点線「この球の1度 111.19km」----
GEO_DEG = dict(box=(1030, 330, 1830, 925), cap=(1062, 372, 44), label_x=1062, label_size=44, track_x=1340, track_w=420, val_size=46, bar_h=44,
               rows=[450, 585, 720])
AXIS_DEG = (109.0, 112.0)
DEG_BARS = [  # (上の名札, 値, 棒の中の値, 名札の時刻, 棒の時刻, 色)。台本「棒「111.2km」「忠敬 110.75km」「今の値 110.95km」」の言葉そのまま
    ("縄・鎖・磁石", RES["degree"][1]["p50"], f"{RES['degree'][1]['p50']:.1f}km", lambda: Sk("c7_b2", 0.0), lambda: Sk("c7_b2", 0.45), BLUE),
    ("忠敬 110.75km", 110.75, "", lambda: Sk("c7_b3", 0.0), lambda: Sk("c7_b3", 0.3), GREEN),
    ("今の値 110.95km", 110.95, "", lambda: Sk("c7_b4", 0.0), lambda: Sk("c7_b4", 0.5), GREEN),
]


def dx_of(v):
    G = GEO_DEG
    return G["track_x"] + (v - AXIS_DEG[0]) / (AXIS_DEG[1] - AXIS_DEG[0]) * G["track_w"]


def panel_deg(ctx, t, a):
    G = GEO_DEG
    draw_box(ctx, G, a)
    text(ctx, "緯度1度の長さ（km）", G["cap"][0], G["cap"][1], G["cap"][2], INK, align="left", alpha=a)
    x0 = G["track_x"]
    draw_poly(ctx, np.array([[x0, 815], [x0 + G["track_w"], 815]]), 3, INK, a * 0.8)
    for v in (109, 110, 111, 112):
        text(ctx, str(v), dx_of(v), 850, 40, INK, alpha=a)
    ta0 = fade(t, Sk("c7_b2", 0.55), 0.5)
    xs = dx_of(RES["true_deg"])
    if ta0 > 0.003:                                                     # 点線: この球の1度（棒と数字の後ろ）
        dotted_line(ctx, xs, 300, xs, 815, RED, 6, a * ta0)
        tag(ctx, "この球の1度 111.19km", 1050, 250, 44, RED, a * ta0, align="left")
    for k, (lab, v, vt, tlf, tbf, col) in enumerate(DEG_BARS):
        y = G["rows"][k]
        text(ctx, lab, G["label_x"], y, G["label_size"], INK, align="left", alpha=a * fade(t, tlf(), 0.4))
        bu = bu_of(t, tbf())
        wd = (dx_of(v) - x0) * bu
        yb = y + 52
        if wd > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.92 * a))
            rrect(ctx, x0, yb - G["bar_h"] / 2, wd, G["bar_h"], 6)
            ctx.fill()
            if vt and bu > 0.5:
                text(ctx, vt, dx_of(v) - 16, yb, G["val_size"], "#ffffff", align="right", alpha=a * clamp01((bu - 0.5) / 0.3))
    text(ctx, "（目もりは 109 から）", 1830 - 24, 905, 40, PENCIL_T, align="right", bold=False, alpha=a)


def draw_panel(ctx, t):
    a_all = out_fade(t, T_ES, 0.4)
    a_big_in = fade(t, S("ch8") + 0.3, 0.5)
    a_small = out_fade(t, T_CMP - 0.2, 0.4) * (1 - a_big_in)
    a_deg = fade(t, S("ch7") + 0.3, 0.5) * out_fade(t, S("ch8") - 0.1, 0.4)
    grp(ctx, a_all * a_small, panel_small, t, 1.0)
    grp(ctx, a_all * a_deg, panel_deg, t, 1.0)
    grp(ctx, a_all * a_big_in, panel_big, t, 1.0)


# ============================================================
# 章カード・終了画面・全体
# ============================================================
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"
LCX_E, RCX_E = 490, 1430


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
    if sub:
        text(ctx, label, 0, -h * 0.31, lsz, INK, alpha=a)
        text(ctx, value, 0, -h * 0.01, vsz, fg, alpha=a)
        text(ctx, sub, 0, h * 0.31, ssz, PENCIL_T, bold=False, alpha=a)
    else:
        text(ctx, label, 0, -h * 0.22, lsz, INK, alpha=a)
        text(ctx, value, 0, h * 0.2, vsz, fg, alpha=a)
    ctx.restore()


def end_rows():
    return [("工夫を足していくと", f"ずれ 約50km → {VAL['L4']:.1f}km", "yellow", INK, -0.010, None),
            ("この方法で 残ったのは", "東西のずれ", "pink", RED, 0.008, None),
            ("正確さは", "歩くだけでは決まらない", "mint", INK, -0.008, None)]


def end_screen(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "歩いて測った日本地図を、1万回 計算したら", LCX_E, 162, 40, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt, sub) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=62, sub=sub, ssz=40)
    tq, t9 = Sk("c8_q", 0.05), S(ID["c8_ch"])
    if t >= tq:
        q = fade(t, tq, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
        if q > 0.003:
            sticky(ctx, "あなたなら、\nもう1つ何を足しますか？", RCX_E, 480, 52, "yellow", a=q, tilt=-0.02)
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


def pages(ctx, t):
    draw_left(ctx, t)
    draw_strip_tags(ctx, t)
    draw_right(ctx, t)
    draw_panel(ctx, t)
    overlays(ctx, t)


def draw(ctx, t):
    lf.spread(ctx)
    if t < T_ES + 0.6:
        grp(ctx, 1 - fade(t, T_ES, 0.5), pages, t)
    if t >= T_ES:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・早回し）
# ============================================================
def BAR_BELLS():
    ts = [Sk("c1_r", 0.6), Sk("c2_r", 0.5), Sk("c3_r", 0.5), Sk("c4_r", 0.5), Sk("c5_r", 0.5), Sk("c7_b2", 0.45), Sk("c7_b3", 0.3), Sk("c7_b4", 0.5)]
    return [(t_ + 0.3, 659.3 if i % 2 else 784.0) for i, t_ in enumerate(ts)]


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 9):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    for g in sorted(GAP_NOTE):
        if g != "g0":
            beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
            mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
    for k_, (tt, f_) in enumerate(BAR_BELLS()):
        mx.add(tt, bell(f_, 1.0), 0.3)
    mx.add(Sk("c8_q", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(S(ID["c8_ch"]) + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
STILL_NAMES = ["① 0.0秒: 題字・問い・歩く点・ずれの数", "② 2.5秒: だいだいの線が本当の線から離れる", "③ 5.0秒: ずれが開いていく・数は伏せる",
               "④ 1章の答え: ずれ 約50km・東西/南北", "⑤ 2章の答え: ずれ 24.4km・東西/南北", "⑥ 3章の答え: ずれ 8.3km",
               "⑦ 4章の答え: ずれ 3.1km・南北 0.7km・東西 2.9km", "⑧ 5章の答え: ずれ 2.2km", "⑨ 6章: 北海道東部（今の地図と伊能図・矢印）",
               "⑩ 6章: 九州南部（今の地図と伊能図・矢印）", "⑪ 7章: 緯度1度の3本の棒", "⑫ まとめ: ずれの棒が5本並ぶ", "⑬ 終了画面"]


def still_times():
    return [0.0, 2.5, 5.0, Ek("c1_ns") + 0.5, Ek("c2_n2") + 0.4, Ek("c3_ew") + 0.5, Ek("c4_ew") + 0.5, Ek("c5_ew") + 0.5,
            Sk("c6_east", 0.5), Ek("c6_kyu") - 1.0, Ek("c7_b4") - 0.2, Ek("c8_ew") + 0.3, S(ID["c8_ch"]) + 2.0]


def _ts(t):
    t = round(t, 1)
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_sheet(out_dir, names_times, thumb=(480, 270), cols=2, label=True):
    from PIL import Image, ImageDraw, ImageFont
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for nm, tt in names_times:
        pth = out_dir / f"{nm}.png"
        lf.still(draw, tt, pth)
        paths.append(pth)
        print(f"  {nm}.png  {_ts(tt)}")
    W_, H_ = thumb
    lab_h, pad = (34 if label else 0), 10
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab_h + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    try:
        fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 26)
    except Exception:
        fnt = ImageFont.load_default()
    for k, p_ in enumerate(paths):
        im = Image.open(p_).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab_h + pad)
        sheet.paste(im, (x, y))
        if label:
            dr.text((x + 4, y + H_ + 3), f"{k + 1}  {_ts(names_times[k][1])}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")
    # 6章の比べる絵（北海道東部・九州南部）を横に2枚（各 480px 幅）
    a_, b_ = Image.open(paths[8]).convert("RGB").resize((480, 270), Image.LANCZOS), Image.open(paths[9]).convert("RGB").resize((480, 270), Image.LANCZOS)
    cmp_ = Image.new("RGB", (960, 270))
    cmp_.paste(a_, (0, 0))
    cmp_.paste(b_, (480, 0))
    cmp_.save(out_dir / "ch6_compare_480.png")
    print("6章の比較:", out_dir / "ch6_compare_480.png")


def review_sheet(path):
    """査読用: 0〜40秒を2.5秒ごと＋出典の前・中・後の3コマ（各 480×270）"""
    from PIL import Image, ImageDraw, ImageFont
    WORK.mkdir(parents=True, exist_ok=True)
    ts = [i * 2.5 for i in range(17)] + [CREDIT_T0 - 0.6, (CREDIT_T0 + CREDIT_T1) / 2 + 0.5, CREDIT_T1 + 0.8]
    labs = [f"{_ts(t)}" for t in ts[:17]] + [f"出典の前 {_ts(ts[17])}", f"出典 表示中 {_ts(ts[18])}", f"出典の後 {_ts(ts[19])}"]
    W_, H_, pad, lab = 480, 270, 8, 30
    cols = 4
    rows = (len(ts) + cols - 1) // cols
    sheet = Image.new("RGB", (pad + cols * (W_ + pad), pad + rows * (H_ + lab + pad)), (58, 58, 58))
    dr = ImageDraw.Draw(sheet)
    fnt = ImageFont.truetype(str(ROOT / "fonts" / "KleeOne-SemiBold.ttf"), 22)
    for k, (t, lb) in enumerate(zip(ts, labs)):
        pth = WORK / f"rv_{k:02d}.png"
        lf.still(draw, t, pth)
        im = Image.open(pth).convert("RGB").resize((W_, H_), Image.LANCZOS)
        x, y = pad + (k % cols) * (W_ + pad), pad + (k // cols) * (H_ + lab + pad)
        sheet.paste(im, (x, y))
        dr.text((x + 4, y + H_ + 3), lb, fill=(235, 235, 235), font=fnt)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    print("査読用の一覧:", path)


def stills_preview(out_dir):
    names = [f"still_{i + 1:02d}" for i in range(len(STILL_NAMES))]
    stills_sheet(out_dir, list(zip(names, still_times())))


# ============================================================
# 文字起こし・読み・画面の文字
# ============================================================
def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字「伊能忠敬」と問い・歩く点が引くだいだいの線・ずれの数）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE.get(it.id, '映像だけ')}）")
        else:
            nt = LINE_NOTE.get(it.id)
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}" + (f"  〔画面: {nt}〕" if nt else ""))
    rows.append("")
    rows.append(f"{_ts(T_ES)}〜{_ts(DUR)} 終了画面の区間（左ページに答えの付せん・右ページに問いかけ、亀と「チャンネル登録よろしく」）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    """読みの確認。read_aloud が AivisSpeech を起動するので、--fake-voice のときは読みを作らず、文だけ並べる"""
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            reading = "" if FAKE else "\n    → " + voice.read_aloud(spoken)
            rows.append(f"{it.id}: {shown_}{reading}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


PEOPLE_LOG = []                                      # (x, y, 高さ)。照合用（scan のときだけ溜める）
PEOPLE_ON = [False]
ARROW_LOG = []                                       # 伊能図の矢印 (始点x, 始点y, 終点x, 終点y)。照合用
_walker_raw = walker


def walker(ctx, x, y, h, a=1.0, step=0.0, staff=True):          # noqa: F811  人の大きさを記録する
    if PEOPLE_ON[0] and a > 0.5:
        PEOPLE_LOG.append((x, y, h))
    _walker_raw(ctx, x, y, h, a, step, staff)


def scan(step=0.25, scale=0.25, t_max=None):
    """0.25秒ごとに描いて、画面の文字（字幕を除く）の位置と、描いた旅人の大きさを集める"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int((t_max or DUR) / step)
    PEOPLE_ON[0] = True
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        PEOPLE_LOG.clear()
        ARROW_LOG.clear()
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale, e[6] / scale) for e in core._LOG]
        frames.append((t, ents, [tuple(p) for p in PEOPLE_LOG], [tuple(a_) for a_ in ARROW_LOG]))
        core._LOG = None
    PEOPLE_ON[0] = False
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


# ============================================================
# 場面の照合（台本の合図・声の数字・画面の数字・早回し・旅人の大きさ・伊能図の矢印・文字の重なり・字幕・終了画面・長さ）
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
OVERLAY_OK = set(CH_TITLES)


def _allowed_nums():
    ok = set(range(0, 11)) | {12, 25, 30, 50, 69, 100, 106, 108, 109, 110, 111, 112, 113, 150, 360, 600, 1380, 16}
    ok |= set(range(25, 50))                                  # 緯度の目もり（北緯30〜45度）
    for k in STEP_KEYS:
        st = LAD[k]
        ok |= {round(st["p50"], 1), round(st["ew"], 1), round(st["ns"], 1), float(ihalf(st["p50"]))}
    ok |= {0.3, 0.9, 111.19, 110.75, 110.95, 28.2}
    ok |= {round(RES["degree"][0]["p50"], 1), round(RES["degree"][1]["p50"], 1)}
    ok |= {float(ihalf(counter_val(t_ / 4))) for t_ in range(0, int(N_COUNT_END * 4) + 1)}      # 冒頭の「ずれ」の数（見本1回ぶん）
    return ok


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


def sub_boxes(t):
    """字幕の各行の箱（字幕は文字のログに入らないので、ここで計算する）"""
    s_, a_ = tl.subtitle_at(t)
    out = []
    if s_ and a_ > 0.3:
        lines = lf.wrap_subtitle(s_)
        n = len(lines)
        for i, l_ in enumerate(lines):
            w = text_width(l_, lf.SUB_SIZE)
            y = lf.SUB_Y - lf.SUB_LINE_H * (n - 1) / 2 + i * lf.SUB_LINE_H
            out.append(("字幕: " + l_, lf.W / 2 - w / 2, y - 22, lf.W / 2 + w / 2, y + 22))
    return out


def strict_pairs(frames, shrink=2.0):
    """全コマで、すべての文字の箱（字幕を含む）の交わりを数える。終了画面への切りかえ（T_ES〜+0.6秒）だけは、フェードの重なりなので数えない。章カード（章の題の付せん）は除く"""
    pairs = []
    for f in frames:
        t = f[0]
        if T_ES <= t < T_ES + 0.6:
            continue
        boxes = [(e[0], e[1] + shrink, e[2] + shrink, e[3] - shrink, e[4] - shrink) for e in f[1] if e[0] not in OVERLAY_OK]
        boxes += [(b[0], b[1] + shrink, b[2] + shrink, b[3] - shrink, b[4] - shrink) for b in sub_boxes(t)]
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] == b[0]:
                    continue
                if min(a[3], b[3]) - max(a[1], b[1]) > 0 and min(a[4], b[4]) - max(a[2], b[2]) > 0:
                    pairs.append((t, a[0], b[0]))
    return pairs


def write_overlap_report(frames, pairs, path):
    n_txt = sum(len(f[1]) for f in frames)
    rows = ["# 文字の箱の交わりの機械検査（sims/inoh-long.py --scenecheck が書く）", "",
            f"- 調べたコマ: {len(frames)}（0.25秒ごと・0〜{frames[-1][0]:.1f}秒）／文字の箱（付せん・札・出典・棒の枠の文字・字幕など）のべ {n_txt} 個",
            "- 各コマで、すべての文字の箱（字幕の行を含む）の組を調べ、面積が重なるものを数えた（箱は2px縮めて判定）",
            "- 数えないもの: 章カード（章の頭の2秒だけ出る題の付せん）／終了画面への切りかえ（T_ES〜+0.6秒）。左ページの絵の入れかえは「前が消える→次が出る」の順で、同時には重ならない",
            f"- 出典（海岸線）は左ページの左下: 箱 x {CREDIT_BOX[0]}〜{CREDIT_BOX[2]}・y {CREDIT_BOX[1]}〜{CREDIT_BOX[3]}・{CREDIT_SIZE}px・{CREDIT_T0:.1f}〜{CREDIT_T1:.1f}秒", "",
            f"## 結果: 交わり {len(pairs)} 件（期待は 0）", ""]
    if pairs:
        rows += ["| 時刻 | 文字A | 文字B |", "|---|---|---|"] + [f"| {_ts(t)} | {a} | {b} |" for t, a, b in pairs[:200]]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("overlap_report:", path)


def _near(frames, t):
    return min(frames, key=lambda f: abs(f[0] - t))


def _px_count(t, pred, box=None, scale=0.5):
    """時刻 t の絵を縮めて描き、条件 pred(r,g,b) を満たす画素を数える（box=(x0,y0,x1,y1) は 1920×1080 の座標）"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    core._CUR_T = t
    ctx = cairo.Context(surf)
    ctx.scale(scale, scale)
    draw(ctx, t)
    surf.flush()
    a = np.ndarray((h, w, 4), np.uint8, surf.get_data())[:, :, :3][..., ::-1].astype(int)
    if box:
        x0, y0, x1, y1 = [int(v * scale) for v in box]
        a = a[y0:y1, x0:x1]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int(pred(r, g, b).sum())


def _is_orange(r, g, b):
    return (abs(r - 236) < 28) & (abs(g - 138) < 36) & (abs(b - 46) < 50)


def _is_navy(r, g, b):
    return (r < 70) & (g < 90) & (b > 50) & (b < 140) & (b - r > 15)


def _is_red(r, g, b):
    return (abs(r - 216) < 25) & (abs(g - 67) < 30) & (abs(b - 78) < 30)


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    has = lambda k, s_: s_ in txt(k)
    checks = []
    A = checks.append
    L0, L1, L2, L3, L4 = (LAD[k] for k in STEP_KEYS)
    # ---- 台本の読み込み ----
    A((f"台本: 章は9つ（0〜8）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる",
       float(len(CHAPS) == 9 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS)), 1, 0))
    A(("台本: 「- 」の行の文言を一字も変えずに読んでいる（声の文を並べ直すと台本の行と同じ。長い文だけ「。」で分けた）",
       float("".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line")), 1, 0))
    A(("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]), 0.5, 1e-6))
    A(("台本: 冒頭に無音の区間はない（0章はどの文のあとも約0.3秒・数字の息つぎなし）", float("g0" not in GAP_NOTE and all(abs(S(b) - E(a) - 0.3) < 1e-6 for a, b in zip(["c0_%d" % i for i in range(0, 9)], ["c0_%d" % i for i in range(1, 10)]) if a in tl._t and b in tl._t)), 1, 0))
    A((f"声（最初の1文）「ずれが約{ihalf(LAD['L0']['p50'])}km」「{ihalf(LAD['L4']['p50'])}kmほどまで縮みます」＝ data.json（目分量の真ん中 {LAD['L0']['p50']:.1f}km・縄・鎖の段 {LAD['L4']['p50']:.1f}km）",
       float(f"約{ihalf(LAD['L0']['p50'])}km" in txt("c0_q") and f"{ihalf(LAD['L4']['p50'])}kmほど" in txt("c0_q")), 1, 0))
    A((f"台本: 無音（早回し）の区間は 1・2・3・4・5章の5つ（0章・7章は無音なし。{sorted(GAP_NOTE)}）", float(sorted(GAP_NOTE) == ["g1", "g2", "g3", "g4", "g5"]), 1, 0))
    # ---- 声の数字 = data.json ----
    exp = [
        ("c1_r", f"約{ihalf(L0['p50'])}km"), ("c1_ew", f"約{ihalf(L0['ew'])}km"), ("c1_ns", f"約{ihalf(L0['ns'])}km"),
        ("c2_r", f"{L1['p50']:.1f}km"), ("c2_n2", f"{L1['ns']:.1f}km"), ("c2_n2", f"{L1['ew']:.1f}km"), ("c2_half", f"約{ihalf(L0['p50'])}km"),
        ("c3_r", f"{L2['p50']:.1f}km"), ("c3_ew", f"{L2['ew']:.1f}km"), ("c3_ns", f"{L2['ns']:.1f}km"),
        ("c3_km25", f"約{ihalf(L0['p50'] - L1['p50'])}km"), ("c3_km16", f"約{ihalf(L1['p50'] - L2['p50'])}km"),
        ("c4_r", f"{L3['p50']:.1f}km"), ("c4_ns", f"{L2['ns']:.1f}km"), ("c4_ns", f"{L3['ns']:.1f}km"), ("c4_ew", f"{L3['ew']:.1f}km"),
        ("c5_r", f"{L4['p50']:.1f}km"), ("c5_ew", f"{L4['ew']:.1f}km"),
        ("c7_b2", f"{RES['degree'][1]['p50']:.1f}km"), ("c7_b3", "110.75km"), ("c7_b4", "110.95km"),
        ("c8_1", f"約{ihalf(L0['p50'])}km"), ("c8_1", f"{L4['p50']:.1f}km"),
    ]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A((f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", float(not bad_), 1, 0))
    A(("声「ほぼ半分」＝ 24.4/49.8 ＝ 0.49 ／「およそ3分の1」＝ 8.3/24.4 ＝ 0.34 ／ 磁石・星の減る割合はほぼ同じ（66%・62%）",
       float(has("c2_half", "ほぼ半分") and has("c3_third", "3分の1") and 0.45 < L1["p50"] / L0["p50"] < 0.55 and 0.30 < L2["p50"] / L1["p50"] < 0.37
             and abs((1 - L2["p50"] / L1["p50"]) - (1 - L3["p50"] / L2["p50"])) < 0.06), 1, 0))
    dg = RES["degree"]
    A(("声「111.2km」＝ 縄・鎖と磁石（段4）の緯度1度の真ん中 111.20km（この球の値と0.01km以内）／「0.2%ほど」＝ (110.95−110.75)/110.95 ＝ 0.18%",
       float(has("c7_ball", "ほぼ戻ります") and abs(dg[1]["p50"] - RES["true_deg"]) < 0.05 and has("c7_b4", "0.2%ほど") and 0.15 < (110.95 - 110.75) / 110.95 * 100 < 0.25), 1, 0))
    A(("声の数字と棒: 棒の値 ＝ data.json の真ん中（約50・24.4・8.3・3.1・2.2）・単調に減る ／ 緯度1度の棒 110.0・111.2・110.75・110.95・点線 111.19",
       float(VTXT == ["約50", "24.4", "8.3", "3.1", "2.2"] and all(VAL[a] > VAL[b] for a, b in zip(STEP_KEYS, STEP_KEYS[1:]))
             and [b[2] for b in DEG_BARS][0] == "111.2km" and [b[0] for b in DEG_BARS][1:] == ["忠敬 110.75km", "今の値 110.95km"] and f"{RES['true_deg']:.2f}" == "111.19"), 1, 0))
    A(("棒の長さ（枠の幅 ＝ 50km）: 約50km は枠いっぱい・2.2km はその4.4%・ch7 の軸は 109〜112km（110.0 → 棒が軸の1/3）",
       float(abs(VAL["L0"] / VMAX - 0.996) < 0.01 and abs(VAL["L4"] / VMAX - 0.044) < 0.001 and abs((dx_of(110.0) - dx_of(109.0)) / (dx_of(112.0) - dx_of(109.0)) - 1 / 3) < 1e-9), 1, 0))
    # ---- 見本・道すじ ----
    A(("絵の見本: 各段30本（460点＝3点に1点）・本当の道すじ（紺）と同じ点数・第4章の見本は星で直す前→後（x は同じ）",
       float(all(len(SAMP[k]) == 30 and len(SAMP[k][0]) == len(TRUE_PX) for k in STEP_KEYS) and RES["pair"]["x_same"] and len(PAIR_B) == 12), 1, 0))
    A((f"絵: 紺（本当の道すじ）はカンバスの左ページに収まる（x {TRUE_PX[:, 0].min():.0f}〜{TRUE_PX[:, 0].max():.0f}・y {TRUE_PX[:, 1].min():.0f}〜{TRUE_PX[:, 1].max():.0f}）・1kmあたり {MS:.2f}画素",
       float(TRUE_PX[:, 0].min() > LBOX[0] and TRUE_PX[:, 0].max() < LBOX[2] and TRUE_PX[:, 1].min() > LBOX[1] and TRUE_PX[:, 1].max() < LBOX[3]), 1, 0))
    # ---- 冒頭 0〜5秒 ----
    i5 = int(clamp01(5.0 / T_WALK) * (len(OPEN_DEV) - 1))
    A((f"冒頭: 5秒目には、歩く点（だいだい）が本当の道すじから {OPEN_DEV[i5]:.0f}km（{OPEN_DEV[i5] * MS:.0f}画素）離れている（20km以上）", float(OPEN_DEV[i5] >= 20), 1, 0))
    c05, c3 = counter_val(0.5), counter_val(N_COUNT_END - 0.05)
    A((f"冒頭: 「ずれ ○km」の数が増えていく（0.5秒 {ihalf(c05)}km → 3秒 {ihalf(c3)}km）・{N_COUNT_END}秒で「？」に伏せる", float(ihalf(c3) >= ihalf(c05) + 8 and 3.0 < N_COUNT_END < 5.0), 1, 0))
    # ---- 声の数字の数（冒頭40秒）----
    first40 = []
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            first40 += [x for x in _re.findall(NUM_RE, tl.clip(it.id).text) if x != "1800"]
    A((f"冒頭40秒で声に出す数字は3つまで（1800年をのぞく）: {first40}", float(len(first40) <= 3), 1, 0))
    # ---- 早回し・時間割 ----
    for gid in ("g1", "g2", "g3", "g5"):
        A((f"早回し {gid}: だいだいの束が無音の区間のうちに20本そろう（1本1.3秒 ≦ 区間 {dur(gid):.1f}秒）", float(dur(gid) >= 1.3 + 0.5), 1, 0))
    A(("4章: 星の印は「30kmごと」の文から出て、描き直し（束が南北にだけ動く）は無音の区間のうちに終わる", float(Sk("c4_30") < S("g4") and dur("g4") >= 2.0), 1, 0))
    A(("7章: 山（縄・鎖と磁石の1万回の1度の長さ）と棒は台本の3文のあいだに順に出る（111.2km → 忠敬 110.75km → 今の値 110.95km）・7章は10秒以上",
       float(Sk("c7_b2") < Sk("c7_b3") <= Sk("c7_b4") and S("ch8") - S("ch7") >= 10), 1, 0))
    # ---- 字幕 ----
    worst_cps, worst_vis, worst_lines = 0.0, 1e9, 0
    for s_, e_, pause, ln, clip in tl._lines:
        vis = e_ - s_ + min(pause, lf.SUB_HOLD)
        worst_cps = max(worst_cps, len(clip.text) / vis)
        worst_vis = min(worst_vis, vis)
        worst_lines = max(worst_lines, len(lf.wrap_subtitle(clip.text)))
    A((f"字幕: 1秒あたりの字数が12字以下（最大 {worst_cps:.1f}字）", float(worst_cps <= 12), 1, 0))
    A((f"字幕: どの行も1秒以上出る（最短 {worst_vis:.1f}秒）", float(worst_vis >= 1.0), 1, 0))
    A((f"字幕: 2行以内（最大 {worst_lines}行）", float(worst_lines <= 2), 1, 0))
    # ---- 章・長さ ----
    ch = tl.chapters
    ends = [c[0] for c in ch[1:]] + [DUR]
    A(("章は9つ・最初は0秒", float(len(ch) == 9 and ch[0][0] == 0), 1, 0))
    for (t0_, title), e_ in zip(ch, ends):
        A((f"章「{title}」が10秒以上", float(e_ - t0_ >= 10), 1, 0))
    A((f"長さ {lf._mmss(DUR)}（--fake-voice の見積もり。本番の声の長さで変わる。6分〜13分）", DUR, 570.0, 210.0))
    A(("終了画面は まとめ の章の中・まとめの最後の説明（正確さは…）は終了画面の前に言い終わる・問いかけは終了画面のあと",
       float(T_ES > S("ch8") + 3 and Ek("c8_end") <= T_ES and T_ES < Sk("c8_q")), 1, 0))
    all_voice = " ".join(tl.clip(i).text for i in LINES)
    bad_words = ("4万", "完成させ", "ぴったり", "GPS", "歩いただけで正確")
    A((f"声に出さない言葉: {[w for w in bad_words if w in all_voice]}", float(not [w for w in bad_words if w in all_voice]), 1, 0))
    # ---- 伊能図（位置合わせ・矢印）----
    for key, nm in (("hokkaido", "北海道東部"), ("kyushu", "九州南部")):
        sh = INO["sheets"][key]
        g = cmp_geo(key)
        sd = [v["sd"] for v in sh["grid"]["hl"].values()] + [v["sd"] for v in sh["grid"]["vl"].values()]
        lat_l = g["lat"][1][1] - g["lat"][0][1] if len(g["lat"]) >= 2 else 0
        m_, _lc, _lo, _k = ino_frame(key)
        gh = sorted((int(k_), v["co"][0] + v["co"][1] * sh["grid"]["size"][0] / 2) for k_, v in sh["grid"]["hl"].items())
        lat_r = (gh[0][1] - gh[1][1]) * INO_SC                                 # 右の伊能図の、緯度1度ぶんの画素（上の緯線−下の緯線）
        A((f"伊能図 {nm}: 左の今の地図は右の画像と同じ縮尺（緯度1度ぶんの画素 左 {abs(lat_l):.1f}・右 {abs(lat_r):.1f}・差2%以内）・北が上・幅 {g['w']}画素（650以上）",
           float(abs(abs(lat_l) - abs(lat_r)) / abs(lat_r) < 0.02 and g["w"] >= 650 and g["h"] <= 810), 1, 0))
        A((f"伊能図 {nm}: 経緯線のあてはめ {len(sh['grid']['hl'])}+{len(sh['grid']['vl'])}本・岬などの地点 {len(sh['points'])}（今の位置は地球地図日本・伊能図の位置は図の経緯線から）",
           float(len(sh["grid"]["hl"]) >= 3 and len(sh["grid"]["vl"]) >= 4 and len(sh["points"]) >= 3), 1, 0))
        east = [p for p in sh["points"] if p["east"]]
        A((f"伊能図 {nm}: 矢印は『伊能図の位置が今の位置より東』の地点だけ（{len(east)}/{len(sh['points'])}）・向き（東）＝ 実測の東西のずれの向き（伊能図の緯度経度が今の位置より東）",
           float(all(p["ino_ll"][1] > p["modern"][1] for p in east) and all((p["ew_km"] > 0.5) == p["east"] for p in sh["points"])), 1, 0))
        md = (OUT / "ino_offsets.md").read_text(encoding="utf-8")
        A((f"伊能図 {nm}: 実測のずれが ino_offsets.md に全地点ぶん書いてある（km は画面に出さない）", float(all(p["name"] in md for p in sh["points"])), 1, 0))
    A(("伊能図: 出典の字幕（キャプション）の言葉 ＝ 「日本沿海輿地図（中図）北海道東部／九州南部　東京国立博物館所蔵　出典: ColBase」", float(CAPTION_INO["hokkaido"] + "／九州南部" == CAPTION_INO["hokkaido"] + "／" + CAPTION_INO["kyushu"][len("日本沿海輿地図（中図）"):]
                                                                   and CAPTION_INO2 == "東京国立博物館所蔵　出典: ColBase" and "ColBase" in CREDIT_INO), 1, 0))
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]
        screen_txt = " ".join(e[0] for _t, e in allt)
        hit_w = [w for w in bad_words if w in screen_txt]
        A((f"画面に出さない言葉: {hit_w}", float(not hit_w), 1, 0))
        bad = overlaps(frames)
        for k, t in list(bad.items())[:12]:
            print(f"  重なり: {_ts(t)} 「{k[0]}」と「{k[1]}」")
        A((f"文字どうしの重なりなし（0.5秒以上続くもの。章カードは除く）: {len(bad)}組", float(len(bad) == 0), 1, 0))
        sp = strict_pairs(frames)
        write_overlap_report(frames, sp, OUT / "overlap_report.md")
        for t_, a_, b_ in sp[:12]:
            print(f"  文字の箱の交わり: {_ts(t_)} 「{a_}」と「{b_}」")
        A((f"全コマ（0.25秒ごと）で、すべての文字の箱（付せん・札・出典・棒の枠の文字・字幕）が交わらない（overlap_report.md）: {len(sp)}件", float(len(sp) == 0), 1, 0))
        small = {}
        for f in frames:
            for e in f[1]:
                if e[5] < 39.5 and e[0] not in CREDIT_LINES:                    # 出典の3行だけは 28px 以上（上の照合）
                    small.setdefault((e[0], round(e[5])), f[0])
        for (s_, sz), t_ in list(small.items())[:12]:
            print(f"  40px未満の文字: {_ts(t_)} 「{s_}」 {sz}px")
        A((f"画面の文字（字幕を除く）は すべて 40px 以上（幅480pxに縮めても読める）: 40px未満 {len(small)}種", float(not small), 1, 0))
        br = [(f[0], e[0]) for f in frames for e in f[1] if e[3] > 1660 and e[4] > 930]
        A((f"右下（x>1660・y>930）に文字を置かない: {len(br)}件", float(not br), 1, 0))
        low = [(f[0], e[0]) for f in frames for e in f[1] if e[4] > 938]
        for t, s_ in low[:5]:
            print(f"  字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        A((f"字幕の帯（y>938）に絵の文字を入れない: {len(low)}件", float(not low), 1, 0))
        stray = [(f[0], e[0]) for f in frames for e in f[1] if f[0] < T_ES and e[0] not in OVERLAY_OK and (945 < e[3] and e[1] < 1030)]
        for t, s_ in stray[:5]:
            print(f"  のどにかかる文字: {_ts(t)} 「{s_}」")
        A((f"見開きののど（x 945〜1030）に文字をまたがせない: {len(stray)}件", float(not stray), 1, 0))
        out_ = [(f[0], e[0]) for f in frames for e in f[1] if f[0] < T_ES and e[0] not in OVERLAY_OK and (e[1] < 40 or e[3] > 1880)]
        for t, s_ in out_[:5]:
            print(f"  ページの端にかかる文字: {_ts(t)} 「{s_}」")
        A((f"文字はページの左右の端（x<40・x>1880）にかからない: {len(out_)}件", float(not out_), 1, 0))
        # 0.0秒目
        f0 = frames[0]
        n0 = {e[0] for e in f0[1]}
        qsz = [e[5] for e in f0[1] if e[0] in QLINES]
        A(("0.0秒目: 題字「伊能忠敬」・右ページの問い（題名と同じ言葉）・「ずれ」の枠が出ている",
           float({"伊能忠敬", "ずれ"} <= n0 and set(QLINES) <= n0 and "".join(QLINES) == "歩いて測った日本地図は、どこまで正確になる？"), 1, 0))
        A((f"0〜5秒: 右ページの問いは 90px 以上（{min(qsz) if qsz else 0:.0f}px）で、4秒まで出ている", float(bool(qsz) and min(qsz) >= 89.5 and all(set(QLINES) <= {e[0] for e in f[1]} for f in frames if f[0] <= 5.0)), 1, 0))
        T05 = [f for f in frames if f[0] <= 5.0]
        A(("0〜5秒: 後ろ姿の旅人が毎コマ描かれている（顔なし・高さ120px以上）", float(all(len(f[2]) >= 1 and max(p[2] for p in f[2]) >= 119 for f in T05)), 1, 0))
        cnt = [any(_re.fullmatch(r"\d+", e[0]) and e[1] > 1400 and 560 < e[2] < 720 for e in f[1]) for f in frames if 0.5 <= f[0] <= 3.0]
        hid = [any(e[0] == "？" for e in f[1]) for f in frames if 3.5 <= f[0] <= 5.0]
        A(("0〜5秒: 右の「ずれ」の数が 0.5〜3秒は数字・3.5〜5秒は「？」（数は途中で伏せる）", float(all(cnt) and all(hid)), 1, 0))
        o5 = _px_count(5.0, _is_orange, (45, 36, 935, 936))
        n5 = _px_count(5.0, _is_navy, (45, 36, 935, 936))
        o0 = _px_count(0.2, _is_orange, (45, 36, 935, 936))
        A((f"冒頭の絵: 0.2秒目より5秒目のほうが、だいだいの線（{o0}→{o5}画素）が長く、紺の道すじ（{n5}画素）が最初から見えている", float(o5 > o0 + 150 and n5 > 800), 1, 0))
        # 人の大きさ
        smallp = sorted({round(p[2]) for f in frames for p in f[2] if p[2] < 119})
        A((f"絵: 旅人（人）はどの場面でも高さ120px以上（小さい人 {smallp}）", float(not smallp and any(f[2] for f in frames)), 1, 0))
        # 台本の〔 〕の「 」の言葉
        tokens = []
        for k_, nt in LINE_NOTE.items():
            for tk in _re.findall(r"「([^」]*)」", nt):
                tokens.append((k_, tk))
        shown = {e[0] for _t, e in allt}
        subst = {"同 九州南部": CAPTION_INO["kyushu"], "東京国立博物館所蔵　出典: ColBase（https://colbase.nich.go.jp/）": CAPTION_INO2}
        miss = sorted({tk for _k, tk in tokens if subst.get(tk, tk) not in shown})
        A((f"台本の画面の指示〔 〕の「 」の言葉 {len(tokens)}個（{len(set(t_ for _k, t_ in tokens))}種）が、すべて画面に文字として出る（出典の字幕は URL をのぞいた形）: 出ていない {miss}", float(not miss), 1, 0))
        late = []
        for k_, tk in tokens:
            ts = [t_ for t_, e in allt if e[0] == subst.get(tk, tk)]
            if tk == "同 九州南部":                                   # 北海道東部のあと、九州南部に切りかわったところで出る
                if not ts or min(ts) > T_CMP2 + 1.0:
                    late.append((k_, tk, round(min(ts), 1) if ts else None))
            elif ts and not (min(ts) <= E(k_) + 3.0):
                late.append((k_, tk, round(min(ts), 1)))
        A((f"台本の〔 〕の言葉は、その文が終わって3秒以内には画面に出ている: 遅れ {late}", float(not late), 1, 0))
        # 数字
        ok_nums = _allowed_nums()
        extra = {}
        for t_, e in allt:
            if e[0] in OVERLAY_OK:
                continue
            for m in _re.findall(NUM_RE, e[0]):
                v = float(m.replace(",", ""))
                if v not in ok_nums:
                    extra.setdefault(v, e[0])
        for v, s_ in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」")
        A((f"画面に出る数字は、すべて data.json の値（の四捨五入）か、目もりなどの閉じた値: 余分 {len(extra)}個", float(not extra), 1, 0))

        def seen(tok, t_a, t_b):
            return any(e[0] == tok for t_, e in allt if t_a <= t_ <= t_b)

        def win(tok_list, a, b):
            return all(seen(x, a, b) for x in tok_list)
        A(("0章: 「江戸」「北海道」の札・「1万回」「ずれ」の付せん・海岸線の出典（2行）・左の凡例（本当の道すじ・描いた線）が出る",
           float(win(["江戸", "北海道", "1万回", "ずれ", *CREDIT_LINES, "本当の道すじ", "描いた線"], 0, S("ch1"))), 1, 0))
        cr = [(t_, e) for t_, e in allt if e[0] in CREDIT_LINES]
        cr_t = sorted({t_ for t_, _e in cr})
        span_ok = bool(cr_t) and cr_t[-1] - cr_t[0] <= 20 and all(t_ < S("ch1") for t_ in cr_t) and min(e[5] for _t, e in cr) >= 27.5
        A((f"出典（海岸線）は画面に1回だけ（0章の中・左ページの左下・{cr_t[0]:.1f}〜{cr_t[-1]:.1f}秒・{CREDIT_SIZE}px・28px以上）・3行をつなぐと「{CREDIT_COAST}」"
           if cr_t else "出典（海岸線）が画面にない", float(span_ok and "".join(CREDIT_LINES) == CREDIT_COAST and all(e[3] < 945 for _t, e in cr)), 1, 0))
        A(("1章: 付せん「出発点」「距離 150m」「方位 8度」「ぶれの大きさはこの動画の置き方」・1本目の棒「目分量」約50・左の札「ずれ 約50km」「東西 21.7km」「南北 36.7km」・1km区間の図（北・方位・距離）",
           float(win(["出発点", "距離 150m", "方位 8度", "ぶれの大きさはこの動画の置き方", "目分量", "約50", "ずれ 約50km", "東西 21.7km", "南北 36.7km", "方位", "距離", "北"], S("ch1"), S("ch2"))), 1, 0))
        A(("2章: 付せん「約69cm（推定）」「距離 50m」・棒「＋歩幅」24.4・左の札「ずれ 24.4km」「東西」「南北」「東西 19.1km」「南北 10.0km」・矢印の図（南北に出る・東西に出る）",
           float(win(["約69cm（推定）", "距離 50m", "＋歩幅", "24.4", "ずれ 24.4km", "東西", "南北", "東西 19.1km", "南北 10.0km", "南北に出る", "東西に出る"], S("ch2"), S("ch3"))), 1, 0))
        A(("3章: 杖先方位盤の絵・付せん「6分の1度まで読める」「方位 0.3度」「割合では向きが効いた」・棒「＋磁石」8.3・左の札「ずれ 8.3km」「東西 2.9km」「南北 7.3km」・図2つ（距離のずれ・向きのずれ）",
           float(win(["杖先方位盤", "6分の1度まで読める", "方位 0.3度", "割合では向きが効いた", "＋磁石", "8.3", "ずれ 8.3km", "東西 2.9km", "南北 7.3km", "距離のずれ", "向きのずれ"], S("ch3"), S("ch4"))), 1, 0))
        A(("4章: 星と象限儀の絵・付せん「星のぶれ 0.9km」「30kmごとに星」・棒「＋星」3.1・左の札「ずれ 3.1km」「南北 7.3km」→「南北 0.7km」「東西 2.9km」",
           float(win(["象限儀", "星のぶれ 0.9km", "30kmごとに星", "＋星", "3.1", "ずれ 3.1km", "南北 7.3km", "南北 0.7km", "東西 2.9km"], S("ch4"), S("ch5"))), 1, 0))
        A(("5章: 縄と鎖の絵・付せん「間縄」「鉄鎖」「もし縄・鎖なら」「距離 10m」・棒「＋縄・鎖」2.2・左の札「ずれ 2.2km」「東西 1.9km」",
           float(win(["麻の縄", "間縄", "鉄鎖", "もし縄・鎖なら", "距離 10m", "＋縄・鎖", "2.2", "ずれ 2.2km", "東西 1.9km"], S("ch5"), S("ch6"))), 1, 0))
        A(("6章: 地球の図（同じ緯度の線・東西の人）・付せん・伊能図2枚（北海道東部・九州南部）の字幕・今の地図の岬の名前（納沙布岬・襟裳岬・知床岬・佐多岬・屋久島・種子島）が出る",
           float(win(["同じ緯度の線", "東にいる人", "西にいる人", "星の高さは 同じ", "時刻が 江戸と違う", CAPTION_INO["hokkaido"], CAPTION_INO["kyushu"], CAPTION_INO2,
                      "納沙布岬", "襟裳岬", "知床岬", "佐多岬", "屋久島", "種子島", "今の地図（北が上）", "伊能図ではここ"], S("ch6"), S("ch7"))), 1, 0))
        small4 = [e[0] for f in frames for e in f[1] if S("ch6") <= f[0] < S("ch7") and e[0] in ("星を見る回数を 変えてみた", "ずれは ほとんど変わらない", "星を見る回数")]
        A((f"6章: 星の間隔の4つの小さな地図は出さない（台本から消えた）: {sorted(set(small4))}", float(not small4), 1, 0))
        kmc = sorted({e[0] for t_, e in allt if T_CMP + 0.6 <= t_ < S("ch7") and "km" in e[0]})
        A((f"6章: 実際の伊能図の場面に km の数字を出さない（台本: 実際の伊能図はずれの km を言わない）: {kmc}", float(not kmc), 1, 0))
        rh = _px_count(Sk("c6_east", 0.5), _is_red, (130, 36, 860, 836)) - _px_count(T_CMP + 0.5, _is_red, (130, 36, 860, 836))
        rk = _px_count(Ek("c6_kyu") - 1.0, _is_red, (130, 36, 860, 836)) - _px_count(T_CMP2 + 0.2, _is_red, (130, 36, 860, 836))
        A((f"6章: 今の地図の側に、東向きの太い赤い矢印が出る（赤い画素の増え 北海道 {rh}・九州 {rk}）", float(rh > 700 and rk > 250), 1, 0))
        alog = {}
        for f in frames:
            for k_, x0_, y0_, x1_, y1_ in f[3] if len(f) > 3 else []:
                alog[(k_, round(x0_), round(y0_))] = (x1_ - x0_, y1_ - y0_)
        nh = sum(1 for k_ in alog if k_[0] == "hokkaido")
        nk = sum(1 for k_ in alog if k_[0] == "kyushu")
        A((f"6章: 矢印は今の地図の側だけ（左ページ x<945）・すべて東向き（x が増える）・北海道 {nh} 本・九州 {nk} 本・太さ10px（480pxに縮めても約2.5px）",
           float(nh == 3 and nk == 5 and all(dx_ > 0 for dx_, dy_ in alog.values()) and all(k_[1] < 945 for k_ in alog)), 1, 0))
        A(("6章: 各シートに「伊能図ではここ」の札が1つ出る・今の地図の名前と北緯の目もりの文字は 40px 以上",
           float(sum(1 for t_, e in allt if e[0] == "伊能図ではここ" and t_ < S("ch7")) > 0 and min(e[5] for t_, e in allt if T_CMP <= t_ < S("ch7") and (e[0].startswith("北緯") or e[0] in ("納沙布岬", "襟裳岬", "知床岬", "佐多岬", "屋久島", "種子島"))) >= 39.5), 1, 0))
        A(("7章: 付せん「緯度1度の長さ」・地球の図（緯度1度・×360）・点線＋札「この球の1度 111.19km」・山の図（縄・鎖＋磁石の向き）・棒「111.2km」「忠敬 110.75km」「今の値 110.95km」",
           float(win(["緯度1度の長さ", "緯度1度", "この長さ × 360 ＝ 地球1周", "この球の1度 111.19km", "縄・鎖＋磁石の向き", "縄・鎖・磁石", "111.2km", "忠敬 110.75km", "今の値 110.95km"], S("ch7"), S("ch8"))), 1, 0))
        f8 = _near(frames, T_ES - 0.3)
        n8 = {e[0] for e in f8[1]}
        A(("8章（まとめ）: ずれの棒が5本並ぶ（目分量 約50 → ＋歩幅 24.4 → ＋磁石 8.3 → ＋星 3.1 → ＋縄・鎖 2.2）・左ページに地図は出さない（大きな数字「約50km」「2.2km」だけ）",
           float({"目分量", "＋歩幅", "＋磁石", "＋星", "＋縄・鎖", "約50", "24.4", "8.3", "3.1", "2.2", "約50km", "2.2km"} <= n8 and not ({"本当の道すじ", "描いた線"} & n8)), 1, 0))
        g_ = _px_count(T_ES - 0.3, _is_orange, (45, 36, 935, 936))
        A((f"8章: 左ページに地図の線（だいだい・紺）が出ない（だいだいの画素 {g_}は大きな数字「2.2km」の文字ぶんだけ）", float(g_ < 6000 and _px_count(T_ES - 0.3, _is_navy, (45, 36, 935, 936)) < 6000), 1, 0))
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936]
        for t, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        A((f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", float(not out_es), 1, 0))
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A((f"終了画面の文字は すべて 38px 以上: {es_small}", float(not es_small), 1, 0))
        ans = [r[1] for r in end_rows()]
        es_ans = {e[0]: e[5] for f in frames if f[0] >= T_ES + 1.0 for e in f[1] if e[0] in ans}
        A((f"終了画面の答えの付せん（左ページ）の答えの文字は 60px 以上: {es_ans}", float(len(es_ans) == 3 and min(es_ans.values()) >= 59.5), 1, 0))
        es_last = [e for f in frames if f[0] >= S(ID["c8_ch"]) + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        A(("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", float(len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5), 1, 0))
        q_ = {e[0] for f in frames if f[0] >= Sk("c8_q", 0.3) for e in f[1]}
        A(("終了画面の問いかけ（あなたなら、もう1つ何を足しますか？）が出る", float({"あなたなら、", "もう1つ何を足しますか？"} <= q_), 1, 0))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--anchors" in args:
        for k_ in ID:
            print(k_, f"{Sk(k_):.1f}-{Ek(k_):.1f}")
        for g_ in sorted(GAP_NOTE):
            print(g_, f"{S(g_):.1f}-{E(g_):.1f}")
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
            frames = scan()
            pk.write_bytes(pickle.dumps(frames))
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, WORK / f"at_{tt:06.1f}.png")
                print("  ", WORK / f"at_{tt:06.1f}.png")
        else:
            stills_preview(OUT / "stills_preview")
        return
    if "--review24" in args:
        review_sheet(OUT / "stills_preview" / "review_0024.png")
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
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    # ---- 本番（AivisSpeech の声つき。この段階ではまだ実行しない）----
    frames = scan()
    scene_checks(frames)
    write_screen_text(OUT / "screen_text.txt", frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
