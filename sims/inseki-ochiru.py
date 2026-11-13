"""隕石が1万個落ちて、人の住む所に当たるのは何個？ 「1万個の雨」を1万セット。— 2026-10-31（公開予定 11.13・ナレーションなし・45秒前後）

くらべるのは「1セット（隕石1万個）のうち、町（建物のある土地）に当たった個数 k」。1万セットの中央値で答えを決める。

【計算の前に固定した条件】（この下の数字は 1万セットを回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  1セット : 隕石 1万個。1個ずつ、地表のどこに落ちるかを引く。落ちた点の土地の種類は 海（湖を含む）・氷・砂漠など・森や草原など・畑や牧場・町 の6つ。
  地図    : Natural Earth（パブリックドメイン）の 1:50m「Natural Earth I」（陸と水の境・陸の色合い）を 0.2度の格子（1800×900）にして使う。
           陸の色合いから 氷／砂漠など／畑や牧場／森や草原など を分けた。**場所のならびは 色合いからの見立て**で、
           **全体の割合は 出典の数字に合わせた**: 氷は地図の白い所（陸の約11.7%。出典の約10%に近い）、砂漠など＝陸の19%（Our World in Data）、
           畑や牧場＝陸の33%（FAO の農地48百万km²÷陸地。Our World in Data）。残り（陸の約36%）が 森や草原など。
           （海と湖＝地表の71.0%、陸＝29.0%は 地図から出た値）
  町     : 「人の住む所」＝建物のある土地。**陸のうち建物のある土地の割合 f は 1セットごとに でたらめに変える**:
           f = 0.5%〜2.1% を 対数で一様に（Chakraborty ほか 2024 Nature Communications 15:9165 が 全球の8つの土地被覆データを比べた幅。
           いちばん小さい WSF 2019 が 0.52%、いちばん大きい Esri が 2.07%、8つの平均 0.95%）。f の置き方を1つに決められないので 幅で回す。
           町の場所は Natural Earth の「都市域」（MODIS 由来・全球で約105万km²＝陸の0.71%）の輪郭を 約0.6度（約70km）ぼかして広げたもの
           （都市の外の郊外・集落のかわり）を 重みにして、全体の量が f になるよう 1セットごとに 重みの大きさを合わせる。町の外の土地は 重みの分だけ 減る。
  落ちる場所: 地表の面積に比例（どこでも同じ確率）。ただし **緯度による偏り**（赤道寄りが多い）を 1セットごとに でたらめに入れる:
           Evatt ほか 2020 Geology（南極の隕石から）は 「極の落下頻度は赤道の約65%」とした。ただし反対意見もある（数点を除くと消える）。
           そこで 極÷赤道の比 r を 0.65〜1.0 から一様に引く（r=1 なら偏りなし）。落ちやすさ g(緯度) = 1 − (1 − r)·sin²(緯度)（式の形は この計算の仮定）。
  数え方 : 1セット 1万個を 個ごとに 引いて 数える。1万セットぶん（1億個）を 回す。

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  1セットで町に当たった数 k の 1万セットの中央値（1万セットを小さい順に並べた ちょうど5,000番目と5,001番目の平均）で決める。
  k < 100 → 100個より少ない ／ 100 ≤ k < 1,000 → 数百個 ／ k ≥ 1,000 → 1,000個以上

【あわせて出す数字】
  ・町に当たった数の 中央値・いちばん少ないセット・いちばん多いセット
  ・ひねり: 「畑や牧場まで入れると？」＝（町＋畑や牧場）に当たった数の 中央値
  ・1万セットの 町の数の ばらつきの内訳: 運（同じ置き方でも 毎回ちがう）と 置き方（f・r）のどちらが大きいか（情報）

【絵について】計算は1万個のまま。絵は 地図に 1万個ぶんの点を 落として積む（点＝1個・1コマの点は小さい）。町に当たった点だけ 赤く大きく描く。
  見本の1回は 1万セットの中の1回（町の数が 1万セットの中央値に近く、f・r が真ん中に近いセット）。同じ乱数で 点の場所を 引き直す。
  怖がらせない: 落ちた跡は 小さな点とかすかな光だけ。都市名は 出さない。

問い: 「隕石が1万個落ちて、/ 人の住む所に / 当たるのは何個？」
      選択肢: 100個より少ない ／ 数百個 ／ 1,000個以上（正解の記号が A）
見せ方: 見本の1セット（点が降る）→ 1万セットの町の数（棒グラフ）→「中央値は ○個・いちばん少ない○・いちばん多い○」
ひねり: 「では、畑や牧場まで入れると？」
締め: 「あなたの答えは、いくつでしたか？」
言葉: 「中央値」は初出で「1万セットの ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。画面に「計算での見立て」を小さく1回。
"""
import hashlib
import io
import math
import struct
import sys
import zipfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "inseki-ochiru"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG
SRC = OUT / "src"

# ---- MODEL BEGIN ----
N_SET = 10000                                        # セットの数
N_DROP = 10000                                       # 1セットの隕石の数
SEED_MAIN = 20261113
NR, NC = 900, 1800                                   # 格子（0.2度）
PIX = 6                                              # 1格子 = 6×6 画素（NE の 1/30度の画素）
CELL_DEG = 0.2
F_LO, F_HI = 0.005, 0.021                            # 陸のうち 建物のある土地の割合（対数で一様）
R_LO, R_HI = 0.65, 1.0                               # 極÷赤道の落ちやすさ（一様）
BARREN_SHARE, FARM_SHARE = 0.19, 0.33                # 陸に占める 砂漠など・畑や牧場（出典の割合）
SMOOTH_SIGMA = 3.0                                   # 都市域のぼかし（格子の数。3×0.2度＝0.6度）
K_ANS = (100, 1000)                                  # 答えの決め方のしきい値
CLS_NAMES = ("海", "氷", "砂漠など", "森や草原など", "畑や牧場", "町")   # 0..5（5＝町）


def answer_by_rule(k_med):
    """k_med: 1セットで町に当たった数の 1万セットの中央値。戻り値は 'few'（100個より少ない）/'some'（数百個）/'many'（1,000個以上）"""
    if k_med < K_ANS[0]:
        return "few"
    if k_med < K_ANS[1]:
        return "some"
    return "many"


def _read_urban_km2():
    """Natural Earth の都市域（shp）を 1/30度の画素に塗り、0.2度の格子ごとの「都市域の面積の割合」にする。戻り値 (B, 合計km²)"""
    from PIL import Image, ImageDraw
    zf = zipfile.ZipFile(SRC / "ne_10m_urban_areas.zip")
    b = zf.read("ne_10m_urban_areas.shp")
    n = len(b)
    o = 100
    KM = 111.195
    PW, PH = NC * PIX, NR * PIX
    img = Image.new("L", (PW, PH), 0)
    dr = ImageDraw.Draw(img)
    small = np.zeros((PH, PW), np.float32)
    tot = 0.0
    while o < n:
        _, cl = struct.unpack(">ii", b[o:o + 8])
        o += 8
        st = struct.unpack("<i", b[o:o + 4])[0]
        if st == 5:
            nparts, npts = struct.unpack("<ii", b[o + 36:o + 44])
            parts = struct.unpack("<%di" % nparts, b[o + 44:o + 44 + 4 * nparts])
            pts = np.frombuffer(b[o + 44 + 4 * nparts:o + 44 + 4 * nparts + 16 * npts], "<f8").reshape(npts, 2)
            for k in range(nparts):
                a = parts[k]
                e = parts[k + 1] if k + 1 < nparts else npts
                x, y = pts[a:e, 0], pts[a:e, 1]
                cosl = math.cos(math.radians(float(y.mean())))
                ar = -0.5 * float(np.sum(x[:-1] * y[1:] - x[1:] * y[:-1])) * KM * KM * cosl     # 外の輪は正・穴は負
                tot += ar
                if 0 < ar < 25.0:                                                                  # 画素より小さい: 面積だけ足す
                    px_km2 = (KM / 30.0) ** 2 * cosl
                    i = min(PH - 1, int((90 - float(y[:-1].mean())) * 30))
                    j = min(PW - 1, int((float(x[:-1].mean()) + 180) * 30))
                    small[i, j] += ar / px_km2
                elif ar != 0:
                    xy = [((float(px) + 180) * 30, (90 - float(py)) * 30) for px, py in zip(x, y)]
                    dr.polygon(xy, fill=255 if ar > 0 else 0)
        o += 2 * cl
    pix = np.asarray(img, np.float32) / 255.0 + small
    pix = np.clip(pix, 0.0, 1.0)
    B = pix.reshape(NR, PIX, NC, PIX).mean(axis=(1, 3))
    lat = 90 - (np.arange(NR) + 0.5) * CELL_DEG
    cell_km2 = (CELL_DEG * KM) ** 2 * np.cos(np.radians(lat))
    B = B * (tot / float((B * cell_km2[:, None]).sum()))          # 塗りの縁で 面積が増えるので、輪の面積の合計（shoelace）に合わせる
    return np.clip(B, 0.0, 1.0).astype(np.float32), float(tot)


def build_grid():
    """地図（色→種類）と 都市域の重み。重いので out/<slug>/cache/ に置く"""
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    Image.MAX_IMAGE_PIXELS = None
    zf = zipfile.ZipFile(SRC / "NE1_50M_SR_W.zip")
    im = np.asarray(Image.open(io.BytesIO(zf.read("NE1_50M_SR_W/NE1_50M_SR_W.tif"))).convert("RGB"))
    H, W = im.shape[:2]
    assert (H, W) == (NR * PIX, NC * PIX)
    R = im[:, :, 0].astype(np.int16)
    G = im[:, :, 1].astype(np.int16)
    B = im[:, :, 2].astype(np.int16)
    water = (B - R >= 40) & (R < 160)
    ice = (~water) & (R >= 215) & (B >= R) & (G >= 215)
    land = ~water
    lat = 90 - (np.arange(H) + 0.5) * (180 / H)
    wt = np.cos(np.radians(lat))[:, None] * np.ones((1, W))
    tot_land = float((wt * land).sum())
    m = (G - R) - 0.5 * (R - B)                                   # 低い＝茶色っぽい（砂漠）、高い＝緑（森）
    sel = land & ~ice
    ms = m[sel]
    o = np.argsort(ms)
    ms = ms[o]
    cw = np.cumsum(wt[sel][o]) / tot_land
    ice_share = float((wt * ice).sum() / tot_land)
    thr_b = ms[min(len(ms) - 1, np.searchsorted(cw, BARREN_SHARE))]
    thr_f = ms[min(len(ms) - 1, np.searchsorted(cw, BARREN_SHARE + FARM_SHARE))]
    cls = np.zeros((H, W), np.uint8)                              # 0 海 1 氷 2 砂漠など 3 畑や牧場 4 森や草原など
    cls[ice] = 1
    cls[sel & (m < thr_b)] = 2
    cls[sel & (m >= thr_b) & (m < thr_f)] = 3
    cls[sel & (m >= thr_f)] = 4
    comp = np.zeros((5, NR, NC), np.uint8)                       # 格子ごとの 画素の数（0〜36）
    for k in range(5):
        comp[k] = (cls == k).reshape(NR, PIX, NC, PIX).sum(axis=(1, 3))
    Bu, urban_km2 = _read_urban_km2()
    return comp, Bu, urban_km2, ice_share


def make_grid(comp, Bu):
    """計算に使う配列。comp=格子の画素数, Bu=都市域の面積割合"""
    from scipy.ndimage import gaussian_filter
    lat_c = 90 - (np.arange(NR) + 0.5) * CELL_DEG
    lat_t = 90 - np.arange(NR) * CELL_DEG
    lat_b = 90 - (np.arange(NR) + 1) * CELL_DEG
    a_row = np.sin(np.radians(lat_t)) - np.sin(np.radians(lat_b))     # 行の面積に比例
    L = 1.0 - comp[0].astype(np.float64) / (PIX * PIX)                # 格子の陸（氷を含む）の割合
    num = gaussian_filter(Bu.astype(np.float64), sigma=SMOOTH_SIGMA, mode=("nearest", "wrap"))
    den = gaussian_filter(L, sigma=SMOOTH_SIGMA, mode=("nearest", "wrap"))
    rho = np.where(L > 0, num / np.maximum(den, 1e-9), 0.0)           # 近くの陸のうち 都市域だった割合（ぼかし）
    rho = np.clip(rho, 0.0, 1.0)
    rho *= (a_row[:, None] * Bu).sum() / (a_row[:, None] * rho * L).sum()
    D = rho * L
    Rt = rho                                                          # 陸の点が町になる確率の重み
    ccum = np.cumsum(comp, axis=0)[:4].astype(np.uint8)               # 海|氷|砂漠|畑 までの累計（森＝残り）
    land_a = float((a_row[:, None] * L).sum())
    s_grid = np.geomspace(0.2, 80.0, 200)
    F = np.array([float((a_row[:, None] * L * np.minimum(1.0, s * Rt)).sum() / land_a) for s in s_grid])
    return dict(a_row=a_row, lat_c=lat_c, L=L, D=D, Rt=Rt, ccum=ccum, land_a=land_a, s_grid=s_grid, F=F)


def s_of_f(G, f):
    """陸のうち町になる割合が f になるような 重みの大きさ s"""
    return float(np.exp(np.interp(f, G["F"], np.log(G["s_grid"]))))


def tilt_weights(G, r):
    """行ごとの 落ちる確率（累計）。g = 1 − (1−r)·sin²(緯度)"""
    g = 1.0 - (1.0 - r) * np.sin(np.radians(G["lat_c"])) ** 2
    return np.cumsum(G["a_row"] * g)


def run_set(G, rng, rec=False, fixed=None):
    """1セット（隕石1万個）。fixed=(f, r) なら その値（感度・確認用）。戻り値 dict(counts[6], f, r, s, ...)"""
    if fixed is None:
        r = float(rng.uniform(R_LO, R_HI))
        f = float(np.exp(rng.uniform(math.log(F_LO), math.log(F_HI))))
    else:
        f, r = fixed
    s = s_of_f(G, f)
    cum = tilt_weights(G, r)
    row = np.searchsorted(cum, rng.random(N_DROP) * cum[-1])
    row = np.minimum(row, NR - 1)
    col = rng.integers(0, NC, N_DROP)
    yy = rng.random(N_DROP)
    xx = rng.random(N_DROP)
    v = rng.integers(0, PIX * PIX, N_DROP)
    u3 = rng.random(N_DROP)
    cc = G["ccum"][:, row, col]
    cls = (v >= cc[0]).astype(np.int8) + (v >= cc[1]) + (v >= cc[2]) + (v >= cc[3])   # 0 海 1 氷 2 砂漠 3 畑 4 森
    pt = np.minimum(1.0, s * G["Rt"][row, col])
    town = (cls > 0) & (u3 < pt)
    cls = np.where(town, 5, cls).astype(np.int8)
    out = dict(counts=np.bincount(cls, minlength=6).astype(np.int32), f=f, r=r, s=s)
    if rec:
        out.update(cls=cls, lat=90 - (row + yy) * CELL_DEG, lon=-180 + (col + xx) * CELL_DEG, row=row, col=col, v=v)
    return out


def run_many(G, seed, n, fixed=None):
    counts = np.zeros((n, 6), np.int32)
    fs = np.zeros(n)
    rs = np.zeros(n)
    for h in range(n):
        o = run_set(G, np.random.default_rng([seed, h]), fixed=fixed)
        counts[h], fs[h], rs[h] = o["counts"], o["f"], o["r"]
    return dict(counts=counts, f=fs, r=rs)


def p_town_analytic(G, f, r):
    """（確認用）1個が町に当たる確率を 引き方とは別に 格子の配列から直接出す"""
    s = s_of_f(G, f)
    g = 1.0 - (1.0 - r) * np.sin(np.radians(G["lat_c"])) ** 2
    w = G["a_row"] * g
    w = w / w.sum()
    pl = G["L"] * np.minimum(1.0, s * G["Rt"])      # 格子の中で 町になる割合（陸の画素のうち。海は町にならない）
    ocean = 1.0 - G["L"]
    del ocean
    return float((w[:, None] * pl).sum() / NC)


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def grid():
    if "G" in _RES:
        return _RES["G"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / "grid_v2.npz"
    if f.exists():
        z = np.load(f)
        comp, Bu, urban_km2, ice_share = z["comp"], z["Bu"], float(z["urban_km2"]), float(z["ice_share"])
    else:
        import time
        t0 = time.time()
        comp, Bu, urban_km2, ice_share = build_grid()
        print(f"  地図の格子 {time.time() - t0:.0f}秒")
        np.savez_compressed(f, comp=comp, Bu=Bu, urban_km2=urban_km2, ice_share=ice_share)
    G = make_grid(comp, Bu)
    G.update(comp=comp, Bu=Bu, urban_km2=urban_km2, ice_share=ice_share)
    _RES["G"] = G
    return G


def results():
    """1万セット。out/<slug>/cache/ に置く"""
    if "m" in _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    G = grid()
    f = cache_dir(SLUG) / f"sets_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        main = {k: z[k] for k in z.files}
    else:
        import time
        t0 = time.time()
        main = run_many(G, SEED_MAIN, N_SET)
        print(f"  1万セット {time.time() - t0:.0f}秒")
        np.savez_compressed(f, **main)
    k = main["counts"][:, 5].astype(np.int64)
    k2 = main["counts"][:, 5] + main["counts"][:, 3]
    _RES["m"] = dict(main=main, k=k, k_med=float(np.median(k)), k_min=int(k.min()), k_max=int(k.max()),
                     k2=k2.astype(np.int64), k2_med=float(np.median(k2)))
    return _RES["m"]


def report():
    G = grid()
    r = results()
    m, k = r["main"], r["k"]
    key = answer_by_rule(r["k_med"])
    cnt = m["counts"]
    print(f"乱数の種 {SEED_MAIN}  {N_SET}セット × {N_DROP}個")
    L = G["L"]
    land_share = float((G["a_row"][:, None] * L).sum() / (G["a_row"].sum() * NC))
    print(f"  地図: 陸 {land_share:.3%}  海 {1 - land_share:.3%}  氷（陸の中）{G['ice_share']:.2%}")
    sh = [float((G["a_row"][:, None] * G["comp"][i] / (PIX * PIX)).sum() / (G["a_row"].sum() * NC)) for i in range(5)]
    ld = sum(sh[1:])
    print("  種類の割合（陸の中）: 氷 {:.1%} 砂漠など {:.1%} 畑や牧場 {:.1%} 森や草原など {:.1%}".format(sh[1] / ld, sh[2] / ld, sh[3] / ld, sh[4] / ld))
    print(f"  都市域（NE）: {G['urban_km2'] / 1e6:.3f} 百万km²  陸の {G['urban_km2'] / (ld * 510.1e6):.3%}")
    print(f"  町の重みの最大（陸の点が町になる確率の重み Rt）{G['Rt'].max():.3f}  s の幅 {s_of_f(G, F_LO):.2f}〜{s_of_f(G, F_HI):.2f}")
    print(f"  k（町に当たった数）: 中央値 {r['k_med']:.1f}  最小 {r['k_min']}  最大 {r['k_max']}  平均 {k.mean():.1f}  → {key}")
    print(f"     四分位 {np.percentile(k, 25):.0f}〜{np.percentile(k, 75):.0f}  5〜95% {np.percentile(k, 5):.0f}〜{np.percentile(k, 95):.0f}  100個以上のセット {int((k >= 100).sum())}")
    print(f"  ひねり（町＋畑や牧場）: 中央値 {r['k2_med']:.0f}  最小 {r['k2'].min()}  最大 {r['k2'].max()}   畑や牧場のみ 中央値 {np.median(cnt[:, 3]):.0f}")
    print(f"  ほかの種類の中央値: 海 {np.median(cnt[:, 0]):.0f} 氷 {np.median(cnt[:, 1]):.0f} 砂漠など {np.median(cnt[:, 2]):.0f} 森や草原など {np.median(cnt[:, 4]):.0f}")
    print(f"  f の中央値 {np.median(m['f']):.4f}  r の平均 {m['r'].mean():.3f}")


def report_sensitivity(n=1500):
    G = grid()
    print(f"感度（f・r を固定して 各{n}セット。運だけのばらつき・情報）:")
    for nm, fx in (("f=0.5% r=1.0", (0.005, 1.0)), ("f=0.5% r=0.65", (0.005, 0.65)), ("f=1.0% r=1.0", (0.010, 1.0)),
                   ("f=1.0% r=0.825", (0.010, 0.825)), ("f=2.1% r=1.0", (0.021, 1.0)), ("f=2.1% r=0.65", (0.021, 0.65))):
        mm = run_many(G, SEED_MAIN + 7, n, fixed=fx)
        k = mm["counts"][:, 5]
        print(f"  {nm}: 町 中央値 {np.median(k):.0f}  最小 {k.min()}  最大 {k.max()}  1個が町に当たる確率（式）{p_town_analytic(G, *fx):.4%}  → {answer_by_rule(np.median(k))}")
    r = results()
    k, f_, r_ = r["k"], r["main"]["f"], r["main"]["r"]
    print(f"  1万セットの k のばらつきのうち、f で説明される分（相関の2乗）{np.corrcoef(np.log(f_), k)[0, 1] ** 2:.2f}  r で {np.corrcoef(r_, k)[0, 1] ** 2:.2f}")


# ---- MODEL END ----


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    if "--nosens" not in sys.argv:
        report_sensitivity()
    sys.exit(0)

# =====================================================================
# 見本（絵に出す1回）を、1万セットの中から選ぶ
# =====================================================================
_SAMPLE = {}


def samples():
    """町に当たった数が 1万セットの中央値と同じで、f・r が真ん中に近い 1セット。1万セットの中の1セットそのもの（同じ乱数で 点の場所を引き直す）"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    G = grid()
    m = r["main"]
    k = r["k"]
    kmed = int(round(r["k_med"]))
    ids = np.nonzero(k == kmed)[0]
    f_med = float(np.median(m["f"]))
    sc = np.abs(np.log(m["f"][ids] / f_med)) + np.abs(m["r"][ids] - 0.5 * (R_LO + R_HI)) / 0.35
    h = int(ids[np.argmin(sc)])
    rec = run_set(G, np.random.default_rng([SEED_MAIN, h]), rec=True)
    cls = rec["cls"]
    onehot = np.zeros((6, N_DROP + 1), np.int32)
    for c in range(6):
        onehot[c, 1:] = np.cumsum(cls == c)
    _SAMPLE.update(h=h, rec=rec, cls=cls, cumc=onehot, town_idx=np.nonzero(cls == 5)[0])
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    S = samples()
    rr = results()
    print(f"見本: セット #{S['h']}  f={S['rec']['f']:.4f}  r={S['rec']['r']:.3f}  町 {int(S['cumc'][5, -1])}個（1万セットの中央値 {rr['k_med']:.0f}）  種類の数 {S['cumc'][:, -1].tolist()}")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, chord, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, whoosh)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.13"                                  # 日付欄（公開予定日）

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は A（1番目）
LABELS = ["100個より少ない", "数百個", "1,000個以上"]
KEY_LABEL = {"few": "100個より少ない", "some": "数百個", "many": "1,000個以上"}
CORRECT = 0                                          # answer_by_rule の結果の位置（A）

BIG_Q3 = ["隕石が1万個落ちて、", "人の住む所に", "当たるのは何個？"]          # 1コマ目の3行（同じ大きさ）
BIG_Q = ["隕石が1万個落ちて、", "人の住む所に当たるのは何個？"]               # 定位置（上）の2行
DETAIL_RULE = "町＝建物のある土地（陸の0.5〜2.1%の幅で回す）"
DETAIL = "これは数のたとえ話。落ちる場所は地表のどこでもほぼ同じ確率"

DOT_COL = ["#2b6fa6", "#8aa0b8", "#9a6a2a", "#e08a00", "#1e7a3c"]            # 点の色（海・氷・砂漠など・畑や牧場・森や草原など）
BASE_COL = ["#d3e8f4", "#f7fafc", "#efdcb4", "#f6edb0", "#c4e0b8"]           # 地図の地の色（うすい）
TOWN_COL = "#e11d2a"
# 凡例の順（種類の番号 → 名前）
LEG = [(0, "海・湖"), (4, "森や草原など"), (3, "畑や牧場"), (2, "砂漠など"), (1, "氷")]

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 910.0, 620.0
CARD_X = 100.0
CARD_Y_INTRO, CARD_Y_FINAL = 830.0, 600.0
CD_X, CD_Y = 790.0, 970.0
MAP_X, MAP_Y, MW, MH = 12, 12, 886, 596             # カードの中の地図の位置と大きさ
RAIN_DUR = 7.0                                       # 1万個が降る時間
FALL = 0.30                                          # 1個が落ちる時間（秒）
FALL_H = 70.0                                        # 落ちてくる高さ（px）
CHART_X0, CHART_X1 = 100.0, 900.0                    # 棒グラフの横の範囲
CHART_BASE, CHART_H = 1130.0, 380.0
BW = 4                                               # 棒グラフの 1本の幅（個）
K_AXIS = 100                                         # 横軸の右端（個）


def setup():
    global T_R0, T_RE, T_HEND, T_D0, T_D1, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TS1, T_TW2, T_Q, DURATION, SCENES
    T_R0 = T_GO + 0.3                               # 雨のはじまり
    T_RE = T_R0 + RAIN_DUR                          # 最後の1個が落ちる
    T_HEND = T_RE + 0.4
    T_D0 = T_HEND + 3.6                             # 棒グラフへ
    T_D1 = T_D0 + 0.8 + 3.4                         # セットが積み終わる
    T_DN = T_D1 + 0.1                               # 数字1（中央値）
    T_DN2 = T_DN + 2.8                              # 数字2（いちばん少ない・多い）
    T_REV = T_DN2 + 3.0                             # 答え
    T_ANS2 = T_REV + 2.8                            # 理由
    T_TW = T_ANS2 + 3.4                             # ひねり
    T_TS1 = T_TW + 0.8 + 1.8                        # 棒が伸び終わる
    T_TW2 = T_TW + 4.2                              # ひねりの答え
    T_Q = T_TW2 + 3.6                               # 締め
    DURATION = T_Q + 4.8
    SCENES = [("見本の1回（隕石1万個の雨）", T_GO, T_D0), ("1万セットの町の数（答え・理由）", T_D0, T_TW),
              ("ひねり（畑や牧場まで）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def pct1(x):
    return f"{math.floor(x * 1000 + 0.5) / 10:.1f}%"


# ---------- 絵: 地図 ----------
_MAP = {}


def _bgra_surface(arr):
    """arr: (h, w, 4) uint8 の BGRA（事前に掛けたもの）→ cairo 面と 配列（配列は面と同じ寿命で持つ）"""
    buf = np.ascontiguousarray(arr)
    h, w = buf.shape[:2]
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, w, h, w * 4)
    return surf, buf


def base_map():
    """地の色（うすい）の世界地図。格子の画素の割合で 色を混ぜ、MW×MH に縮める"""
    if "base" in _MAP:
        return _MAP["base"]
    from PIL import Image
    G = grid()
    comp = G["comp"].astype(np.float32) / (PIX * PIX)
    rgb = np.zeros((NR, NC, 3), np.float32)
    for k in range(5):
        c = np.array(hexrgb(BASE_COL[k])[:3], np.float32) * 255
        rgb += comp[k][:, :, None] * c[None, None, :]
    im = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((MW, MH), Image.BOX)
    a = np.asarray(im, np.uint8)
    arr = np.zeros((MH, MW, 4), np.uint8)
    arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3] = a[:, :, 2], a[:, :, 1], a[:, :, 0], 255
    _MAP["base"] = _bgra_surface(arr)
    return _MAP["base"]


def drop_xy():
    """見本の 点の位置（地図の画素）"""
    if "xy" not in _MAP:
        S = samples()
        rec = S["rec"]
        _MAP["xy"] = ((rec["lon"] + 180.0) / 360.0 * MW, (90.0 - rec["lat"]) / 180.0 * MH)
    return _MAP["xy"]


def drop_times():
    """i 番目の点が 地表につく時刻。降る数が 時間の2乗で増える（はじめはゆっくり・だんだん雨になる）"""
    if "ti" not in _MAP:
        _MAP["ti"] = T_R0 + RAIN_DUR * np.sqrt((np.arange(N_DROP) + 0.5) / N_DROP)
    return _MAP["ti"]


def n_landed(t):
    return int(np.searchsorted(drop_times(), t, side="right"))


_DOTS = {}


def dots_surface(n):
    """n 個ぶんまで積んだ点の図（海・氷・砂漠・畑・森。町は 別に 大きく描く）"""
    step = 40
    key = n // step if n < N_DROP else -1
    if key in _DOTS:
        return _DOTS[key]
    if len(_DOTS) > 400:
        _DOTS.clear()
    m = N_DROP if n >= N_DROP else (n // step) * step
    S = samples()
    x, y = drop_xy()
    cls = S["cls"][:m]
    px = np.clip(x[:m].astype(int), 1, MW - 2)
    py = np.clip(y[:m].astype(int), 1, MH - 2)
    rgba = np.zeros((MH, MW, 4), np.float32)
    for c in range(5):
        sel = cls == c
        if not sel.any():
            continue
        cnt = np.zeros((MH, MW), np.float32)
        np.add.at(cnt, (py[sel], px[sel]), 1.0)
        big = cnt.copy()                                   # 3×3 に太らせる（点が スマホで見える大きさ）
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy or dx:
                    big += 0.55 * np.roll(np.roll(cnt, dy, 0), dx, 1)
        al = 1.0 - np.exp(-1.2 * big)
        col = np.array(hexrgb(DOT_COL[c])[:3][::-1], np.float32) * 255          # BGR
        rgba[:, :, :3] = rgba[:, :, :3] * (1 - al[:, :, None]) + col[None, None, :] * al[:, :, None]
        rgba[:, :, 3] = rgba[:, :, 3] * (1 - al) + 255 * al
    _DOTS[key] = _bgra_surface(np.clip(rgba, 0, 255).astype(np.uint8))
    return _DOTS[key]


MAP_LABELS = [("太平洋", -150, 12), ("大西洋", -32, 8), ("インド洋", 80, -24), ("アフリカ", 20, 4), ("ユーラシア", 82, 58),
              ("北アメリカ", -102, 46), ("南アメリカ", -58, -16), ("南極", 10, -78)]


def draw_map_card(ctx, t, n=None):
    """カードの中身（地図・点・落ちてくる点・町）。t は動画の秒。n を渡すと 1万個ぜんぶ積んだ絵（締め）"""
    ctx.set_source_surface(base_map()[0], 0, 0)
    ctx.paint()
    S = samples()
    x, y = drop_xy()
    ti = drop_times()
    nl = N_DROP if n is not None else n_landed(t)
    if nl > 0:
        ctx.set_source_surface(dots_surface(nl)[0], 0, 0)
        ctx.paint()
    for nm, lo, la in (MAP_LABELS if n is None else []):           # 大陸・海の名前（小さく）。締めの縮小図には出さない
        text(ctx, nm, (lo + 180) / 360 * MW, (90 - la) / 180 * MH, 26, "#4a5670", bold=False, alpha=0.75 * clamp01((t - 0.6) / 0.25))
    # 落ちてくる点（流れ星の線）
    if n is None and nl < N_DROP:
        j1 = int(np.searchsorted(ti, t + FALL, side="right"))
        if j1 > nl:
            idx = np.arange(nl, j1)
            p = 1.0 - (ti[idx] - t) / FALL                       # 0（空）→ 1（地表）
            hy = y[idx] - (1 - p) * FALL_H
            hx = x[idx] - (1 - p) * FALL_H * 0.35
            ctx.set_source_rgba(1.0, 0.62, 0.18, 0.75)
            ctx.set_line_width(2.2)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            for a_, b_, c_, d_ in zip(hx, hy, hx - 5, hy - 14):
                ctx.move_to(float(a_), float(b_))
                ctx.line_to(float(c_), float(d_))
            ctx.stroke()
    # 町に当たった点（赤く大きく）
    for i in S["town_idx"]:
        tt = ti[i]
        if n is None and t < tt:
            continue
        cx, cy = float(x[i]), float(y[i])
        age = 9.0 if n is not None else t - tt
        if age < 0.7:                                              # かすかな光（輪）
            rad = 9 + 28 * ease_out(age / 0.7)
            ctx.arc(cx, cy, rad, 0, 2 * math.pi)
            ctx.set_source_rgba(1.0, 0.9, 0.5, 0.8 * (1 - age / 0.7))
            ctx.set_line_width(3)
            ctx.stroke()
        ctx.arc(cx, cy, 9.0, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(TOWN_COL))
        ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.set_line_width(2)
        ctx.stroke()


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.75))
    ctx.set_line_width(3.5)
    ctx.stroke()
    ctx.save()
    rrect(ctx, MAP_X, MAP_Y, MW, MH, 14)
    ctx.clip()
    ctx.translate(MAP_X, MAP_Y)
    draw_map_card(ctx, t)
    ctx.restore()
    rrect(ctx, MAP_X, MAP_Y, MW, MH, 14)
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(3.2)
    ctx.stroke()
    rrect(ctx, 24, 22, 530, 82, 12)                     # 題（左上）
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    la = clamp01((t - 0.6) / 0.25)                       # 冒頭の寄りが戻るまで 文字は出さない（左が切れないように）
    text(ctx, "隕石1万個の雨（1セット）", 42, 46, 40, INK, align="left", alpha=la)
    text(ctx, "計算での見立て", 42, 86, 26, PENCIL, align="left", bold=False, alpha=la)
    ctx.restore()


def scene_alpha(t):
    if t < T_D0:
        return 1.0
    return 1 - ease((t - T_D0) / 0.4)


def draw_legend(ctx, t, a):
    """カードの下: 種類ごとの数（左）と 町に当たった数（右）"""
    if a <= 0:
        return
    S = samples()
    n = n_landed(t)
    cc = S["cumc"][:, n]
    for i, (c, nm) in enumerate(LEG):
        y = 1262 + i * 42
        ctx.arc(122, y, 12, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(DOT_COL[c], a))
        ctx.fill()
        text(ctx, nm, 150, y, 32, INK, align="left", bold=False, alpha=a)
        text(ctx, fmt(cc[c]), 560, y, 32, INK, align="right", alpha=a)
    after = t >= T_HEND
    lab = "たとえば、この1回では\n町に当たったのは" if after else "町に当たった数"
    text(ctx, lab, 745, 1300 if after else 1285, 32, INK, bold=False, alpha=a)
    ctx.arc(612, 1395, 11, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(TOWN_COL, a))
    ctx.fill()
    text(ctx, f"{fmt(cc[5])}個", 790, 1392, 100, RED, alpha=a)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.30 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: 場面が寄ったところから引く（下端を基準に）
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
    if t >= T_GO:
        draw_legend(ctx, t, a * ease_out((t - T_GO) / 0.3))


# ---------- 棒グラフ（1万セットの町の数） ----------

def hist_edges():
    return np.arange(0, K_AXIS + BW, BW)


_H = {}


def hist_state(n_sets):
    """最初の n_sets セットまでの 棒グラフ（セットの番号順＝でたらめな順）"""
    r = results()
    k = r["k"]
    ed = hist_edges()
    if "full" not in _H:
        _H["full"] = np.histogram(np.minimum(k, K_AXIS - 1), bins=ed)[0].astype(float)
    key = n_sets // 100
    if key not in _H:
        _H[key] = np.histogram(np.minimum(k[:n_sets], K_AXIS - 1), bins=ed)[0].astype(float)
    return _H[key], _H["full"]


def kx(v):
    """個数 → グラフの x"""
    return CHART_X0 + (CHART_X1 - CHART_X0) * v / K_AXIS


def hist_alpha(t):
    if t < T_D0:
        return 0.0
    return ease((t - T_D0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    k = r["k"]
    text(ctx, "町に当たった数（1万セットぶん）", 560, 622, 36, INK, alpha=a)
    pr = clamp01((t - T_D0 - 0.8) / (T_D1 - T_D0 - 0.8))
    n_sets = N_SET if pr >= 1 else int(N_SET * ease(pr))
    text(ctx, "1セット＝隕石1万個　棒＝そのセットの数", 560, 664, 26, PENCIL, bold=False, alpha=a)
    cnt, full = hist_state(n_sets)
    hmax = full.max()
    ed = hist_edges()
    bwpx = (CHART_X1 - CHART_X0) * BW / K_AXIS
    ctx.move_to(CHART_X0 - 10, CHART_BASE)
    ctx.line_to(CHART_X1 + 10, CHART_BASE)
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
    ctx.set_line_width(3)
    ctx.stroke()
    for i in range(len(cnt)):
        hgt = CHART_H * cnt[i] / hmax
        x = kx(ed[i])
        rrect(ctx, x + 2, CHART_BASE - hgt, bwpx - 4, max(hgt, 0.5), 4)
        ctx.set_source_rgba(*hexrgb(DOT_COL[0], 0.9 * a))
        ctx.fill()
    for v in (0, 20, 40, 60, 80, 100):
        text(ctx, str(v), kx(v), CHART_BASE + 32, 30, INK, bold=False, alpha=a)
    ctx.move_to(kx(K_AXIS), CHART_BASE - CHART_H - 20)                     # 100個の線
    ctx.line_to(kx(K_AXIS), CHART_BASE)
    ctx.set_dash([8, 6])
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.85 * a))
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "100個", kx(K_AXIS) - 4, CHART_BASE - CHART_H - 40, 26, PENCIL, bold=False, alpha=a)
    # 右の空いている所（グラフの中）: セットの数 → 中央値
    if t < T_DN:
        text(ctx, "いま", 740, 800, 28, PENCIL, bold=False, alpha=a)
        text(ctx, fmt(n_sets), 740, 880, 92, INK, alpha=a)
        text(ctx, "/ 10,000 セット目", 740, 960, 30, INK, bold=False, alpha=a)
    else:
        u = ease_out((t - T_DN) / 0.3) * a
        xm = kx(r["k_med"] + 0.5)
        ctx.move_to(xm, CHART_BASE - CHART_H - 14)
        ctx.line_to(xm, CHART_BASE)
        ctx.set_dash([9, 6])
        ctx.set_source_rgba(*hexrgb(RED, 0.95 * u))
        ctx.set_line_width(4)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, "中央値", xm, CHART_BASE - CHART_H - 34, 28, RED, alpha=u)
        text(ctx, "中央値", 740, 800, 36, INK, alpha=u)
        text(ctx, f"{fmt(r['k_med'])}個", 740, 900, 120, RED, alpha=u)
        text(ctx, "（1万セットの\nちょうど真ん中の値）", 740, 1010, 28, PENCIL, bold=False, alpha=u)
    # グラフの下: いちばん少ない・多い（積んでいる間は ここまでの値）
    if t >= T_D0 + 0.8:
        kk = k[:max(n_sets, 1)]
        lo, hi = int(kk.min()), int(kk.max())
        fin = t >= T_DN2
        u = ease_out((t - T_D0 - 0.8) / 0.3) * a
        col = RED if fin else INK
        lab = "いちばん少ない" if fin else "ここまでの最少"
        lab2 = "いちばん多い" if fin else "最多"
        text(ctx, f"{lab}　{fmt(lo)}個　／　{lab2}　{fmt(hi)}個", 500, 1222, 38, col, alpha=u)
    if t < T_REV:
        u2 = ease_out((t - T_D0 - 1.0) / 0.3) * a
        text(ctx, "ばらつきの元は2つ　①運（どこに落ちるか）\n②置き方（町の割合 0.5〜2.1%・赤道寄りの偏り）", 520, 1340, 30, PENCIL,
             bold=False, alpha=u2 * (1 - ease((t - T_REV + 0.3) / 0.3)))


# ---------- ひねり（畑や牧場まで） ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


TW_BAR_X, TW_BAR_W = 100.0, 810.0


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    r = results()
    k1, k2 = r["k_med"], r["k2_med"]
    text(ctx, "1万個のうち 当たった数の中央値", 560, 630, 36, INK, alpha=a)
    pr = ease(clamp01((t - T_TW - 0.8) / (T_TS1 - T_TW - 0.8)))
    rows = ((730, "町だけ", k1, TOWN_COL, 84), (880, "町＋畑や牧場", k2, DOT_COL[3], 130))
    for y, nm, val, col, th in rows:
        text(ctx, nm, TW_BAR_X, y, 38, INK, align="left", alpha=a)
        w = max(TW_BAR_W * val / k2 * pr, 3.0)
        rrect(ctx, TW_BAR_X, y + 34, w, th, 10)
        ctx.set_source_rgba(*hexrgb(col, 0.92 * a))
        ctx.fill()
        txt = f"{fmt(val * pr)}個"
        if val == k2 and w > 340:
            text(ctx, txt, TW_BAR_X + w - 18, y + 34 + th / 2, 72, "#ffffff", align="right", alpha=a)
        else:
            text(ctx, txt, TW_BAR_X + w + 16, y + 34 + th / 2, 64, RED, align="left", alpha=a)


# ---------- 答え ----------

def answer_key():
    return answer_by_rule(results()["k_med"])


def reason_text():
    r = results()
    cnt = r["main"]["counts"]
    sea = float(np.median(cnt[:, 0]))
    town_share = r["k_med"] / N_DROP
    return (f"1万個のうち 約{fmt(sea)}個は 海に落ちる。\n町は 地表の約{pct1(town_share)}しかない。")


TW_Q = "では、畑や牧場まで\n入れると？"


def r_k2_share():
    return results()["k2_med"] / N_DROP


def tw_a():
    r = results()
    return f"畑や牧場まで入れると、{fmt(r['k2_med'])}個に増える。"


def tw_b():
    return "畑や牧場は 陸の約3分の1（FAO）。人がまばらな所も多い。"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"答えは『{KEY_LABEL[key]}』。", 570, 1298, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 570, 1405, 28, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 570, 1135, 46, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        text(ctx, tw_a(), 570, 1300, 36, RED, alpha=e)
        text(ctx, tw_b(), 540, 1362, 26, INK, bold=False, alpha=e)
        text(ctx, f"（1万個のうち 約{pct1(r_k2_share())}）", 570, 1412, 28, PENCIL, bold=False, alpha=e)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に世界地図（0秒目から場面が寄ったところから引く）"""
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


# ---------- 締め ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたの答えは、\nいくつでしたか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 972, 36, INK, bold=False, alpha=r)
    ctx.save()                                                                  # 1万個ぶんの点が積もった地図
    sc = 0.74
    ctx.translate(540 - CARD_W * sc / 2 + 20, 1000)
    ctx.scale(sc, sc)
    ctx.push_group()
    rrect(ctx, 0, 0, CARD_W, CARD_H, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 1.0))
    ctx.fill()
    ctx.save()
    rrect(ctx, MAP_X, MAP_Y, MW, MH, 14)
    ctx.clip()
    ctx.translate(MAP_X, MAP_Y)
    draw_map_card(ctx, T_Q, n=N_DROP)
    ctx.restore()
    rrect(ctx, MAP_X, MAP_Y, MW, MH, 14)
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(3.2)
    ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()


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
    for i in range(4):                                      # 冒頭: ひゅっ・ひゅっ（流れ星）
        mx.add(0.1 + 0.5 * i, blip(900 + 90 * i, 0.06), 0.25)
    S = samples()
    ti = drop_times()
    mx.add(T_R0 - 0.2, riser(1.0), 0.35)
    for j in np.arange(T_R0, T_RE, 0.12):                  # 雨の音（ぱらぱら）。だんだん密に
        u = (j - T_R0) / RAIN_DUR
        mx.add(float(j), blip(float(1500 + 700 * ((j * 37) % 1.0)), 0.03), float(0.05 + 0.10 * u))
    for n_, i in enumerate(S["town_idx"]):                  # 町に当たったときだけ 小さく鐘
        mx.add(float(ti[i]), bell([784.0, 880.0, 988.0, 1046.5][n_ % 4], 0.5), 0.22)
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # 棒グラフ
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
    for i in range(2):
        mx.add(T_TS1 + 0.15 * i, bell([784.0, 988.0][i], 0.8), 0.35)
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


def _class_ref(G, row, col, v):
    """run_set とは別の書き方（1個ずつの普通のループ）で 町でない種類を出す: 海0 氷1 砂漠2 畑3 森4"""
    comp = G["comp"]
    out = np.zeros(len(row), np.int8)
    for i in range(len(row)):
        acc = 0
        c = 4
        for k in range(5):
            acc += int(comp[k, row[i], col[i]])
            if v[i] < acc:
                c = k
                break
        out[i] = c
    return out


def run_checks():
    G = grid()
    r = results()
    m = r["main"]
    cnt = m["counts"]
    k = r["k"]
    checks = []
    # (1) 地図・出典の割合
    L = G["L"]
    land_share = float((G["a_row"][:, None] * L).sum() / (G["a_row"].sum() * NC))
    checks.append(("陸の割合 29%（地図）", land_share, 0.29, 0.005))
    checks.append(("海の割合 71%（地図。約71%）", 1 - land_share, 0.71, 0.005))
    sh = np.array([float((G["a_row"][:, None] * G["comp"][i] / (PIX * PIX)).sum()) for i in range(5)])
    ld = sh[1:].sum()
    checks.append(("陸の中の 砂漠など = 19%（出典）", float(sh[2] / ld), BARREN_SHARE, 0.01))
    checks.append(("陸の中の 畑や牧場 = 33%（FAO の農地÷陸）", float(sh[3] / ld), FARM_SHARE, 0.015))
    checks.append(("陸の中の 氷 は 10〜12%（出典の約10%）", float(0.10 <= sh[1] / ld <= 0.12), 1.0, 0.0))
    checks.append(("格子の画素の数は どこも 36（合計）", float((G["comp"].sum(axis=0) == PIX * PIX).all()), 1.0, 0.0))
    checks.append(("都市域（NE）の面積 100〜110万km²（輪の面積の合計）", float(1.0e6 <= G["urban_km2"] <= 1.10e6), 1.0, 0.0))
    for f_ in (F_LO, 0.01, F_HI):
        s_ = s_of_f(G, f_)
        got = float((G["a_row"][:, None] * L * np.minimum(1.0, s_ * G["Rt"])).sum() / G["land_a"])
        checks.append((f"重みを合わせると 陸のうち町になる割合 = f（f={f_:.3f}）", got, f_, f_ * 0.01))
    checks.append(("町になる確率の重みは 1 以下（ぼかしで 1を超えない）", float(G["Rt"].max() <= 1.0), 1.0, 0.0))
    # (2) 引き方
    checks.append(("セットの数 = 1万", float(len(k)), float(N_SET), 0.0))
    checks.append(("どのセットも 1万個（種類の合計）", float((cnt.sum(axis=1) == N_DROP).all()), 1.0, 0.0))
    checks.append(("f は 0.5%〜2.1%", float(m["f"].min() >= F_LO - 1e-12 and m["f"].max() <= F_HI + 1e-12), 1.0, 0.0))
    checks.append(("f の対数の平均 = 対数の真ん中（一様）", float(np.log(m["f"]).mean()), 0.5 * (math.log(F_LO) + math.log(F_HI)), 0.02))
    checks.append(("r は 0.65〜1.0", float(m["r"].min() >= R_LO and m["r"].max() <= R_HI), 1.0, 0.0))
    checks.append(("r の平均 0.825（一様）", float(m["r"].mean()), 0.825, 0.005))
    for fx in ((0.005, 1.0), (0.01, 0.8), (0.021, 0.65)):                       # 町の数の平均を、格子の配列から直接出した確率と比べる
        mm = run_many(G, 4242, 400, fixed=fx)
        kk = mm["counts"][:, 5]
        pa = p_town_analytic(G, *fx)
        se = math.sqrt(N_DROP * pa * (1 - pa) / 400)
        checks.append((f"町の数の平均が 式（格子から直接）と合う（f={fx[0]}, r={fx[1]}）", float(kk.mean()), N_DROP * pa, 4 * se))
    checks.append(("海に落ちる割合の平均 = 地図の海の割合（偏りで 少し動く）", float(cnt[:, 0].mean() / N_DROP), 1 - land_share, 0.012))
    S = samples()
    rec = S["rec"]
    ref = _class_ref(G, rec["row"][:60], rec["col"][:60], rec["v"][:60])
    got = np.where(rec["cls"][:60] == 5, ref, rec["cls"][:60])              # 町は 町でなかったときの種類に戻して比べる
    checks.append(("種類の判定: 速い計算と 1個ずつのループが同じ（60個）", float((got == ref).sum()), 60.0, 0.0))
    tw = rec["cls"] == 5
    checks.append(("町に当たった点は 陸のある格子の上", float((G["L"][rec["row"][tw], rec["col"][tw]] > 0).all()), 1.0, 0.0))
    # (3) 緯度の偏り
    gl = 1 - (1 - 0.65) * np.sin(np.radians(G["lat_c"])) ** 2
    checks.append(("落ちやすさ: 極 ÷ 赤道 = r（0.65）", float(gl[0] / gl[NR // 2]), 0.65, 0.01))
    # (4) 答え
    key = answer_by_rule(r["k_med"])
    checks.append(("規則の答え = few（100個より少ない）", float(key == "few"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 100個より少ない・数百個・1,000個以上（小さい順）", float(LABELS == ["100個より少ない", "数百個", "1,000個以上"]), 1.0, 0.0))
    for v_, k_ in ((20, "few"), (99, "few"), (100, "some"), (999, "some"), (1000, "many")):
        checks.append((f"規則の道具: k={v_} → {k_}", float(answer_by_rule(v_) == k_), 1.0, 0.0))
    sk = np.sort(k)
    checks.append(("中央値を 並べ替えから数え直しても同じ", float(sk[N_SET // 2 - 1] + sk[N_SET // 2]) / 2, r["k_med"], 1e-9))
    checks.append(("いちばん多いセットも 100個に届かない（棒グラフの軸 0〜100 に収まる）", float(r["k_max"] < K_AXIS), 1.0, 0.0))
    # (5) 見本は1万セットの中の1セットそのもの
    h = S["h"]
    checks.append(("見本: 引き直した 町の数 = 1万セットの記録", float(S["cumc"][5, -1]), float(cnt[h, 5]), 0.0))
    checks.append(("見本: 引き直した 種類ごとの数 = 1万セットの記録（6種類ぜんぶ）", float(np.array_equal(S["cumc"][:, -1], cnt[h])), 1.0, 0.0))
    checks.append(("見本: 町の数 = 1万セットの中央値", float(S["cumc"][5, -1]), r["k_med"], 0.0))
    checks.append(("見本: 画面の数え（降り終わり）= 記録", float(S["cumc"][5, n_landed(T_RE + 0.01)]), float(cnt[h, 5]), 0.0))
    checks.append(("見本: 降り終わりに 1万個ぜんぶ 落ちている", float(n_landed(T_RE + 0.01)), float(N_DROP), 0.0))
    checks.append(("見本: 画面に描く 赤い点の数 = 町の数", float(len(S["town_idx"])), float(cnt[h, 5]), 0.0))
    xx, yy = drop_xy()
    checks.append(("見本: 点はすべて 地図の中", float((xx >= 0).all() and (xx < MW).all() and (yy >= 0).all() and (yy < MH).all()), 1.0, 0.0))
    # (6) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (7) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 見本（降り終わりのあと 次の場面まで）3秒以上", float(T_D0 - T_HEND >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 棒グラフの最後の数字 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: ひねりの棒の数字 3秒以上", float(T_Q - T_TS1 >= 3.0), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (8) 冒頭の動き
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
    print(f"長さ {DURATION:.1f}秒  雨 {T_R0:.1f}〜{T_RE:.1f}  棒グラフ {T_D0:.1f}-{T_D1:.1f}  数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: セット #{S['h']}  f={S['rec']['f']:.4f}  r={S['rec']['r']:.3f}  町 {int(S['cumc'][5, -1])}個  種類 {S['cumc'][:, -1].tolist()}")
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
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_R0 + 0.5, T_R0 + 2.0, T_R0 + 4.0, T_R0 + 5.5, T_RE - 0.3, T_HEND + 0.3, T_HEND + 2.0,
              T_D0 + 0.9, T_D0 + 2.2, T_D1 - 0.1, T_DN + 1.2, T_DN2 + 1.2, T_REV + 0.9, T_ANS2 + 0.6,
              T_TW + 0.8, T_TW + 2.4, T_TS1 + 1.2, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
