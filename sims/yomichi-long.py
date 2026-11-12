"""江戸の夜、あなたは提灯なしで家に帰れる？（横型ロング）— 2026-10-27 作成。前半＝モデル（数字の計算・照合）／後半（「# ここから下は場面」から）＝場面（絵・声の並び・照合・静止画）

構成案: research/longform_yomichi_outline_2026-10-26.md ／ 下調べ: research/longform_edo_yomichi_sources_2026-10-26.md
試算の元: research/edo_yomichi_calc/（year.py の照度の式、moon.py の簡易式）

問い: 江戸の町人が、提灯を持たずに、月明かりだけで夜道を1里（約1時間）歩いて家に帰れるか。

モデル
  場所と時刻  : 日本橋あたり（北緯35.684度・東経139.774度）。時刻は地方平均時（世界時＋9時間19分）。
  1万人      : 1人ずつ、次の順でくじを引く（乱数の種は固定。main_seed）。
                1. 1781〜1868年の、日記の天気が分かる日（「不明」を除く）から1日。どの日も同じ確率。
                2. 出る時刻を「暮六つ 〜 （夜四つ − 60分）」から一様に（1分刻みの整数分）。
                3. 空のくじ。日ごとに1回だけ引く（下の「空」）。
  歩く       : 1里＝60分。出た時刻から1分刻みで60点、月の照度 E を出す。
  月の照度 E  : 年に1回の試算（year.py）と同じ式。
                E = 0.267 lx × (384400 km ÷ 月の距離)² × 位相係数 × 大気の減光 × sin(月の高度)
                  位相係数    = 10^(−0.4·(0.026·α + 4×10⁻⁹·α⁴))   α＝位相角（度）＝ 180 − 太陽との離角
                  大気の減光 = 10^(−0.4·0.20·X)                 X ＝ 1 ÷ (sin h + 0.025·exp(−11 sin h))
                月の高度 h が 0 度以下なら E = 0。高度は地表から見た値（視差を引く。大気差は入れない）。
  暮六つ・夜四つ: 暮六つ ＝ 太陽の中心が地平線の下 7°21′40″ になる時刻（夕方）。明六つ ＝ 同じ高さになる翌朝の時刻。
                夜四つ ＝ 暮六つ ＋（明六つ − 暮六つ）× 2/6。
  月と太陽の位置: 外部ライブラリなし。Meeus『Astronomical Algorithms』第47章の主要項（月は黄経19項・黄緯8項・距離4項）と
                低精度の太陽の式を自分で写した（ΔT・章動・光行差は入れない）。ephem は --check の照合にだけ使う。
  空         : 日記の「その日の最後の天気」で代用。その日に夜の記述（夜ニ入…・夜中…）があれば、夜の記述を優先する。
                晴 ＝ 見える／陰晴 ＝ 半分の確率で見える／曇・雨雪 ＝ 見えない／雨止 ＝ 半分の確率で見える。
  歩ける線    : 0.05 lx（ふつうの満月くらい・仮定）。E がこの線以上の分が「月明かりで歩けた分」。
  月明かりで歩けた分 : 空が見えていて、E ≥ 線 の分の合計（0〜60）。空が見えない人は 0。
  家まで帰れた : 60分すべてが「歩けた分」。
  旧暦日      : 日記の見出しの旧暦の日（暦そのもの）。--check では「新月を含む日が1日」の計算と比べる。
  季節        : 新暦の月。冬＝12〜2月、春＝3〜5、夏＝6〜8、秋＝9〜11。

数え方
  いちばん悪かった人 : 歩けた分が0の人のうち、旧暦28日以降か1〜2日（晦日ごろ）で、空の記述が雨雪の人。人数と代表1人。
                      代表＝晦日そのもの（その旧暦月の最後の日）の人で、出た時刻が窓の真ん中にいちばん近い人。
  いちばん良かった人 : 空が見える人のうち、60分の照度の平均がいちばん大きい人。
  月の出入り         : 月の上縁が地平線に一致する時刻（地平の大気差34′・半径を入れる。国立天文台の暦と同じ約束）。
  「雲あり」の歩けた分の割合 : 歩けた分の合計 ÷ （人数×60）。「雲なし」は空を無視（いつも見える）した割合。
  厳密計算   : くじを引かず、全部の日×全部の出る時刻を数え上げて平均した値（シミュとは別の経路）。1万人の結果は、この値と
               標準誤差の4倍以内で一致するかを --check で見る。
  幅         : 歩ける線を 0.02 lx にしたとき／日記の晴れの1割を曇り扱いにしたとき（同じ1万人・同じくじで線や確率だけ変える）。
  頑健さ     : 種を5つ変えて1万人をやり直し、主要な数字のばらつきを見る。

照合（--check）
  - 月の出入り: 国立天文台 暦計算室「各地のこよみ 東京 2026年10月」と比べ、数分以内（research/edo_yomichi_calc/nao_tokyo_2026-10_moon.csv）
  - ephem（照合用）: 1845年の数晩で、暮六つ・夜四つ・照度を比べる
  - 自作の簡易式のベクトル版 ＝ 1つずつ書いたスカラー版（同じ式）
  - 1人ずつ書いたスカラー版で200人の歩けた分が一致
  - 1万人の結果 ≒ 厳密計算（標準誤差の4倍以内）
  - 日記の表の整合（連続した日・件数・旧暦日の並び）

使い方
  python -X utf8 sims/yomichi-long.py --compute    計算 → out/yomichi-long/data.json
  python -X utf8 sims/yomichi-long.py --check      照合だけ（ephem は PYTHONPATH に置いてあれば使う）
  python -X utf8 sims/yomichi-long.py --numbers    data.json → out/yomichi-long/numbers.md（data.json が無ければ先に --compute）
  python -X utf8 sims/yomichi-long.py --scenedata  場面で使う1人ぶんの照度の並び（九夜・十五夜・十六夜・冬・梅雨など）→ out/yomichi-long/scene_people.json
                                                   （同じ1万人・同じモデル関数から取り出すだけ。data.json・数字は変えない。無ければ場面が最初に自動で作る）

場面（絵と声の並び。台本 publish/yomichi-long/narration_B.md を読み込む。本番の声での書き出しはまだしない）
  python -X utf8 sims/yomichi-long.py --scenecheck --fake-voice    場面の照合（偽の声・長さは見積もり）
  python -X utf8 sims/yomichi-long.py --stills --fake-voice        要所の静止画と stills_480.png（out/yomichi-long/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
  python -X utf8 sims/yomichi-long.py --readings --fake-voice      読みの確認 / --wraps 字幕の折り返し / --docs 文字起こし・チャプター / --anchors 場面の合図の時刻

天気の表: data/edo_weather/hirosaki_edo_1781_1868.csv（出典は同じフォルダの SOURCE.md）
  ※ CSV は公開していないので、sims/yomichi-weather-build.py で JCDP の江戸日記PDF（https://jcdp.jp/daily-diary-weather-records-jp/）から作る。
    出典: 福眞吉美（2018）地学雑誌 127, 565-568／JCDP「日記天候記録」 https://jcdp.jp/daily-diary-weather-records-jp/
"""
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

SLUG = "yomichi-long"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / SLUG
WEATHER_CSV = ROOT / "data" / "edo_weather" / "hirosaki_edo_1781_1868.csv"
NAO_CSV = ROOT / "research" / "edo_yomichi_calc" / "nao_tokyo_2026-10_moon.csv"

LAT, LON = 35.684, 139.774              # 日本橋あたり
LOC_H = LON / 15                         # 地方平均時 ＝ 世界時 ＋ LOC_H 時間
SUN_DEPR = -(7 + 21 / 60 + 40 / 3600)    # 暮六つ・明六つ ＝ 太陽の中心高度（度）
N = 10000
MAIN_SEED = 2026
ROB_SEEDS = [2027, 2028, 2029, 2030, 2031]
WALK = 60                                # 1里 ＝ 60分
LINE = 0.05                              # 歩ける線（lx）
LINE_LOW = 0.02
CLEAR_CUT = 0.9                          # 日記の晴れを1割減らす → 晴の見える確率 0.9
CLASSES = ["晴", "陰晴", "曇", "雨雪", "雨止"]
P_VIS = np.array([1.0, 0.5, 0.0, 0.0, 0.5])
SEASONS = ["冬(12〜2月)", "春(3〜5月)", "夏(6〜8月)", "秋(9〜11月)"]
SEASON_OF_MONTH = {12: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 2, 7: 2, 8: 2, 9: 3, 10: 3, 11: 3}


def r1(x):
    return float(np.round(x, 1))


# ============================================================
# 月と太陽（Meeus 第47章の主要項。ベクトル版）
# ============================================================
SL = [(6288774, 0, 0, 1, 0), (1274027, 2, 0, -1, 0), (658314, 2, 0, 0, 0), (213618, 0, 0, 2, 0), (-185116, 0, 1, 0, 0),
      (-114332, 0, 0, 0, 2), (58793, 2, 0, -2, 0), (57066, 2, -1, -1, 0), (53322, 2, 0, 1, 0), (45758, 2, -1, 0, 0),
      (-40923, 0, 1, -1, 0), (-34720, 1, 0, 0, 0), (-30383, 0, 1, 1, 0), (15327, 2, 0, 0, -2), (-12528, 0, 0, 1, 2),
      (10980, 0, 0, 1, -2), (10675, 4, 0, -1, 0), (10034, 0, 0, 3, 0), (8548, 4, 0, -2, 0)]
SB = [(5128122, 0, 0, 0, 1), (280602, 0, 0, 1, 1), (277693, 0, 0, 1, -1), (173237, 2, 0, 0, -1), (55413, 2, 0, -1, 1),
      (46271, 2, 0, -1, -1), (32573, 2, 0, 0, 1), (17198, 0, 0, 2, 1)]
SR = [(-20905355, 0, 0, 1, 0), (-3699111, 2, 0, -1, 0), (-2955968, 2, 0, 0, 0), (-569925, 0, 0, 2, 0)]


def moon_state(jd):
    """月の赤経・赤緯（ラジアン）、距離（km）、太陽との離角（度）。jd は世界時のユリウス日（配列可）。"""
    jd = np.asarray(jd, dtype=float)
    T = (jd - 2451545.0) / 36525
    rad = np.radians
    Lp = 218.3164477 + 481267.88123421 * T
    D = 297.8501921 + 445267.1114034 * T
    M = 357.5291092 + 35999.0502909 * T
    Mp = 134.9633964 + 477198.8675055 * T
    F = 93.2720950 + 483202.0175233 * T
    Ec = 1 - 0.002516 * T
    lon = Lp.copy()
    for c, d, m, mp, f in SL:
        lon = lon + c * Ec ** abs(m) * np.sin(rad(d * D + m * M + mp * Mp + f * F)) / 1e6
    lat = np.zeros_like(T)
    for c, d, m, mp, f in SB:
        lat = lat + c * np.sin(rad(d * D + m * M + mp * Mp + f * F)) / 1e6
    dist = np.full_like(T, 385000.56)
    for c, d, m, mp, f in SR:
        dist = dist + c * np.cos(rad(d * D + m * M + mp * Mp + f * F)) / 1000
    eps = rad(23.4392911 - 0.0130042 * T)
    lam = rad(lon % 360)
    beta = rad(lat)
    ra = np.arctan2(np.sin(lam) * np.cos(eps) - np.tan(beta) * np.sin(eps), np.cos(lam))
    dec = np.arcsin(np.sin(beta) * np.cos(eps) + np.cos(beta) * np.sin(eps) * np.sin(lam))
    Ls = 280.46646 + 36000.76983 * T
    Ms = 357.52911 + 35999.05029 * T
    C = (1.914602 - 0.004817 * T) * np.sin(rad(Ms)) + 0.019993 * np.sin(rad(2 * Ms))
    sun_lon = (Ls + C) % 360
    elong = np.degrees(np.arccos(np.clip(np.cos(beta) * np.cos(lam - rad(sun_lon)), -1, 1)))
    return ra, dec, dist, elong


def sun_state(jd):
    jd = np.asarray(jd, dtype=float)
    T = (jd - 2451545.0) / 36525
    rad = np.radians
    Ls = 280.46646 + 36000.76983 * T
    Ms = 357.52911 + 35999.05029 * T
    C = (1.914602 - 0.004817 * T) * np.sin(rad(Ms)) + 0.019993 * np.sin(rad(2 * Ms))
    lam = rad((Ls + C) % 360)
    eps = rad(23.4392911 - 0.0130042 * T)
    return np.arctan2(np.cos(eps) * np.sin(lam), np.cos(lam)), np.arcsin(np.sin(eps) * np.sin(lam))


def _hour_angle_alt(jd, ra, dec, lat, lon):
    T = (jd - 2451545.0) / 36525
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T) % 360
    H = np.radians(gmst + lon) - ra
    la = np.radians(lat)
    return np.arcsin(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(H))


def moon_alt_topo(jd, lat=LAT, lon=LON):
    """月の中心の地表から見た高度（ラジアン）、距離、離角。"""
    ra, dec, dist, el = moon_state(jd)
    alt = _hour_angle_alt(jd, ra, dec, lat, lon)
    alt = alt - np.arcsin(6378.14 / dist) * np.cos(alt)
    return alt, dist, el


def sun_alt(jd, lat=LAT, lon=LON):
    ra, dec = sun_state(jd)
    return np.degrees(_hour_angle_alt(jd, ra, dec, lat, lon))


def moon_light(jd, lat=LAT, lon=LON):
    """月の照度 E（lx）、月の高度 h（度）、離角（度）。"""
    h, dist, el = moon_alt_topo(jd, lat, lon)
    alpha = 180 - el
    ph = 10 ** (-0.4 * (0.026 * alpha + 4e-9 * alpha ** 4))
    s = np.sin(h)
    with np.errstate(all="ignore"):
        X = 1 / (s + 0.025 * np.exp(-11 * s))
        ext = 10 ** (-0.4 * 0.20 * X)
        E = 0.267 * (384400 / dist) ** 2 * ph * ext * s
    return np.where(h > 0, E, 0.0), np.degrees(h), el


def jd_of(ordv, minutes, off_h=LOC_H):
    """グレゴリオ暦の日（date.toordinal）と、その日の0時からの分 → 世界時のユリウス日。off_h ＝ 時計と世界時の差（時間）。"""
    return np.asarray(ordv, dtype=float) + 1721424.5 + np.asarray(minutes, dtype=float) / 1440 - off_h / 24


def solve_sun(ordv, rising):
    """各日の暮六つ（rising=False）または明六つ（True）を、その日の0時からの分で返す。ニュートン法。"""
    ordv = np.asarray(ordv, dtype=float)
    t = np.full(ordv.shape, 360.0 if rising else 1080.0)
    for _ in range(10):
        f = sun_alt(jd_of(ordv, t)) - SUN_DEPR
        df = (sun_alt(jd_of(ordv, t + 1)) - sun_alt(jd_of(ordv, t - 1))) / 2
        t = t - f / df
    return t


def clock(m):
    m = float(m)
    day = int(m // 1440)
    m -= day * 1440
    s = "%02d:%02d" % (int(m // 60), int(m % 60))
    return s if day == 0 else ("翌" + s if day == 1 else "前日" + s)


def moon_events(ordv, lat=LAT, lon=LON, off_h=LOC_H, start=720, end=2160):
    """その日の昼12時から翌日の昼12時までの、月の出・月の入り（月の上縁が地平線に一致・大気差34′）。
    戻り値: [(0 時からの分, 'rise'|'set')]"""
    m = np.arange(start, end + 1, 1.0)
    jd = jd_of(ordv, m, off_h)
    h, dist, _ = moon_alt_topo(jd, lat, lon)
    thr = -np.radians(34 / 60) - np.arcsin(1737.4 / dist)
    g = h - thr
    ev = []
    for i in np.nonzero(np.sign(g[:-1]) != np.sign(g[1:]))[0]:
        x = m[i] + g[i] / (g[i] - g[i + 1])
        ev.append((float(x), "rise" if g[i + 1] > g[i] else "set"))
    return ev


# ============================================================
# 日記の表
# ============================================================
def load_weather():
    import datetime as dt
    rows = []
    with open(WEATHER_CSV, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    n = len(rows)
    ords = np.array([dt.date.fromisoformat(r["date"]).toordinal() for r in rows])
    ld = np.array([int(r["kyureki"].split("月")[1].rstrip("日")) for r in rows])
    last = np.zeros(n, bool)                       # その旧暦月の最後の日（晦日）
    last[:-1] = (ld[1:] == 1)
    month = np.array([int(r["date"][5:7]) for r in rows])
    ci = {c: i for i, c in enumerate(CLASSES)}
    day_cls = np.array([ci.get(r["day_class"], -1) for r in rows])
    night_cls = np.array([ci.get(r["night_class"], -1) for r in rows])
    cls = np.where(night_cls >= 0, night_cls, day_cls)
    return dict(rows=rows, ords=ords, ld=ld, last=last, month=month, day_cls=day_cls, night_cls=night_cls, cls=cls)


class Days:
    """くじの対象になる日（日記の天気が分かる日）の表と、暮六つ・夜四つ・月の照度の1分刻みの格子。"""

    def __init__(self, W):
        ok = W["day_cls"] >= 0
        self.W = W
        self.idx = np.nonzero(ok)[0]
        s = self.idx
        self.ords = W["ords"][s]
        self.ld = W["ld"][s]
        self.last = W["last"][s]
        self.month = W["month"][s]
        self.cls = W["cls"][s]
        self.day_cls = W["day_cls"][s]
        self.night_cls = W["night_cls"][s]
        self.season = np.array([SEASON_OF_MONTH[m] for m in self.month])
        self.nd = len(s)
        self.dusk = solve_sun(self.ords, False)
        dawn = solve_sun(self.ords + 1, True) + 1440
        self.dawn = dawn
        self.yotsu = self.dusk + (dawn - self.dusk) * 2 / 6
        self.span = self.yotsu - WALK - self.dusk            # 出る時刻の幅（分）
        self.noff = np.floor(self.span).astype(int) + 1      # 出る時刻 0..noff-1（暮六つから何分後か）
        self.J = int(self.noff.max()) + WALK - 1
        E = np.zeros((self.nd, self.J), np.float32)
        H = np.zeros((self.nd, self.J), np.float32)
        EL = np.zeros(self.nd)
        step = 1500
        j = np.arange(self.J)
        for a in range(0, self.nd, step):
            b = min(a + step, self.nd)
            mins = self.dusk[a:b, None] + j[None, :]
            jd = jd_of(self.ords[a:b, None], mins)
            e, h, el = moon_light(jd)
            E[a:b] = e
            H[a:b] = h
            EL[a:b] = el[:, 0]
        self.E = E
        self.H = H
        self.el0 = EL

    def p_vis(self, pclear=1.0):
        p = P_VIS.copy()
        p[0] = pclear
        return p[self.cls]


# ============================================================
# 1万人のくじ
# ============================================================
def draw(days, seed, n=N):
    rng = np.random.default_rng(seed)
    di = rng.integers(0, days.nd, n)
    off = (rng.random(n) * days.noff[di]).astype(int)
    u = rng.random(n)
    return di, off, u


def walk_people(days, di, off, u, line=LINE, pclear=1.0):
    k = np.arange(WALK)
    E60 = days.E[di[:, None], off[:, None] + k[None, :]]
    ok = E60 >= line
    vis = u < days.p_vis(pclear)[di]
    nosky = ok.sum(1)
    mins = np.where(vis, nosky, 0)
    return dict(di=di, off=off, u=u, E60=E60, vis=vis, nosky=nosky, mins=mins, home=(mins == WALK))


def headline(days, P):
    """1万人の主要な数字（割合は%）。"""
    d = days
    di = P["di"]
    home = P["home"]
    out = dict(n=int(len(di)), home=100 * home.mean(), mins_mean=float(P["mins"].mean()),
               mins_median=float(np.median(P["mins"])), zero=100 * (P["mins"] == 0).mean())
    ld = d.ld[di]
    for L in range(1, 31):
        m = ld == L
        out[f"lday{L}_n"] = int(m.sum())
        out[f"lday{L}_home"] = 100 * home[m].mean() if m.any() else float("nan")
        out[f"lday{L}_walk"] = 100 * P["mins"][m].sum() / (WALK * m.sum()) if m.any() else float("nan")
        out[f"lday{L}_walk_nocloud"] = 100 * P["nosky"][m].sum() / (WALK * m.sum()) if m.any() else float("nan")
    ss = d.season[di]
    for s in range(4):
        m = ss == s
        out[f"season{s}_n"] = int(m.sum())
        out[f"season{s}_home"] = 100 * home[m].mean()
    out["winter_over_summer"] = out["season0_home"] / out["season2_home"] if out["season2_home"] > 0 else float("nan")
    return out


# ============================================================
# 厳密計算（くじを引かず数え上げる）
# ============================================================
def exact_tables(days, line=LINE, pclear=1.0):
    d = days
    ind = d.E >= line
    cp = np.zeros((d.nd, d.J + 1), np.int16)
    np.cumsum(ind, axis=1, dtype=np.int16, out=cp[:, 1:])
    nmax = d.J - WALK + 1
    Wc = cp[:, WALK:WALK + nmax] - cp[:, :nmax]                     # 出る時刻ごとの歩けた分（空が見えるとき）
    valid = np.arange(nmax)[None, :] < d.noff[:, None]
    wt = (valid / d.noff[:, None]).astype(float)
    idx = (np.arange(d.nd)[:, None] * (WALK + 1) + Wc)[valid]
    pm = np.bincount(idx, weights=wt[valid], minlength=d.nd * (WALK + 1)).reshape(d.nd, WALK + 1)   # 空が見えるときの分の分布
    p = d.p_vis(pclear)
    pmix = p[:, None] * pm
    pmix[:, 0] += 1 - p
    return pm, pmix


def exact_summary(days, line=LINE, pclear=1.0, tab=None):
    d = days
    pm, pmix = tab if tab is not None else exact_tables(days, line, pclear)
    m = np.arange(WALK + 1)
    mean_day = pmix @ m
    nosky_day = pm @ m
    home_day = pmix[:, WALK]
    tot = pmix.mean(0)
    cum = np.cumsum(tot)
    out = dict(home=100 * home_day.mean(), mins_mean=float(mean_day.mean()),
               mins_median=int(np.searchsorted(cum, 0.5)), zero=100 * tot[0])
    for L in range(1, 31):
        s = d.ld == L
        out[f"lday{L}_n"] = int(s.sum())
        out[f"lday{L}_home"] = 100 * home_day[s].mean() if s.any() else float("nan")
        out[f"lday{L}_walk"] = 100 * mean_day[s].mean() / WALK if s.any() else float("nan")
        out[f"lday{L}_walk_nocloud"] = 100 * nosky_day[s].mean() / WALK if s.any() else float("nan")
        # 日記の日どうしのばらつきから見た標準誤差（日記の日を「江戸の天気と月の組み合わせ」の標本と見たとき）
        if s.sum() > 1:
            out[f"lday{L}_home_se"] = 100 * home_day[s].std(ddof=1) / math.sqrt(s.sum())
            out[f"lday{L}_walk_se"] = 100 * mean_day[s].std(ddof=1) / WALK / math.sqrt(s.sum())
            out[f"lday{L}_walk_nocloud_se"] = 100 * nosky_day[s].std(ddof=1) / WALK / math.sqrt(s.sum())
    for k in range(4):
        s = d.season == k
        out[f"season{k}_n"] = int(s.sum())
        out[f"season{k}_home"] = 100 * home_day[s].mean()
        out[f"season{k}_home_se"] = 100 * home_day[s].std(ddof=1) / math.sqrt(s.sum())
    out["winter_over_summer"] = out["season0_home"] / out["season2_home"] if out["season2_home"] > 0 else float("nan")
    return out


def moon_profile(days):
    """旧暦日ごと・季節ごとの、暮六つ〜夜四つの月の高さと照度（厳密）。"""
    d = days
    jlen = d.noff + WALK - 1                       # 暮六つ〜夜四つ（のひとつ手前）の分数
    mask = np.arange(d.J)[None, :] < jlen[:, None]
    Hc = np.where(mask, np.maximum(d.H, 0), 0).sum(1) / jlen        # 月が出ていない分は高さ0
    up = np.where(mask, d.H > 0, False).sum(1) / jlen
    Em = np.where(mask, d.E, 0).sum(1) / jlen
    out = dict(by_lday={}, by_season={})
    for L in range(1, 31):
        s = d.ld == L
        if s.any():
            out["by_lday"][L] = dict(n=int(s.sum()), alt_dusk=float(np.maximum(d.H[s, 0], 0).mean()), alt_mean=float(Hc[s].mean()),
                                     up_share=float(100 * up[s].mean()), E_mean=float(Em[s].mean()))
    for k in range(4):
        s = (d.season == k) & (d.ld >= 13) & (d.ld <= 16)
        t = d.season == k
        out["by_season"][k] = dict(
            n_days=int(t.sum()), clear_day=float(100 * (d.day_cls[t] == 0).mean()), clear_final=float(100 * (d.cls[t] == 0).mean()),
            vis_prob=float(100 * d.p_vis()[t].mean()), n_1316=int(s.sum()), alt_1316=float(Hc[s].mean()),
            up_1316=float(100 * up[s].mean()), E_1316=float(Em[s].mean()),
            window_min=float(((d.yotsu - d.dusk)[t]).mean()))
    return out


# ============================================================
# 代表の2人
# ============================================================
def person_card(days, P, i):
    d = days
    di = int(P["di"][i])
    off = int(P["off"][i])
    ordv = int(d.ords[di])
    row = d.W["rows"][d.idx[di]]
    t0 = d.dusk[di] + off
    tt = t0 + np.arange(WALK)
    jd = jd_of(ordv, tt)
    E, h, el = moon_light(jd)
    ev = moon_events(ordv)
    dd = d.dusk[di]
    ill = 100 * (1 + math.cos(math.radians(180 - float(el[0])))) / 2
    return dict(
        date=row["date"], kyureki=row["kyureki"], lday=int(d.ld[di]), season=SEASONS[int(d.season[di])],
        day_class=row["day_class"], night_class=row["night_class"] or None, sky=CLASSES[int(d.cls[di])],
        sky_visible=bool(P["vis"][i]),
        dusk=clock(dd), yotsu=clock(d.yotsu[di]), depart=clock(t0), depart_after_dusk_min=off, arrive=clock(t0 + WALK),
        moon_events=[(clock(x), k) for x, k in ev], moon_lit_percent=r1(ill),
        moon_alt_at_depart=r1(h[0]), moon_alt_at_arrive=r1(h[-1]), moon_alt_max_in_walk=r1(h.max()),
        E_mean=float(E.mean()), E_max=float(E.max()),
        walkable_min=int(P["mins"][i]), walkable_min_if_visible=int(P["nosky"][i]),
        series=dict(min=list(range(WALK)), E=[float(round(x, 5)) for x in E], moon_alt=[r1(x) for x in h],
                    clock=[clock(x) for x in tt]),
    )


def pick_cards(days, P):
    d = days
    di = P["di"]
    ld = d.ld[di]
    cond = (P["mins"] == 0) & ((ld >= 28) | (ld <= 2)) & (d.cls[di] == 3)
    n_worst = int(cond.sum())
    last = d.last[di]
    cand = np.nonzero(cond & last)[0]
    if len(cand) == 0:
        cand = np.nonzero(cond)[0]
    mid = (P["off"][cand] + 0.5) / d.noff[di[cand]]
    w = int(cand[np.argmin(np.abs(mid - 0.5))])
    effE = P["E60"].mean(1) * P["vis"]
    order = np.argsort(-effE)
    best = [int(x) for x in order[:3]]
    return dict(
        worst_n=n_worst, worst_misoka_n=int((cond & last).sum()), worst_rule="歩けた分0 かつ 旧暦28日以降か1〜2日 かつ 空の記述が雨雪。代表＝晦日そのものの人で出た時刻が窓の真ん中にいちばん近い人",
        worst=person_card(days, P, w), best=person_card(days, P, best[0]),
        best_rank2=person_card(days, P, best[1]), best_rank3=person_card(days, P, best[2]),
        zero_n=int((P["mins"] == 0).sum()))


# ============================================================
# 補助: 旧暦日の計算（新月を含む日が1日）と満月の瞬間
# ============================================================
def _ecl_lon_diff(jd):
    jd = np.asarray(jd, float)
    T = (jd - 2451545.0) / 36525
    rad = np.radians
    Lp = 218.3164477 + 481267.88123421 * T
    D = 297.8501921 + 445267.1114034 * T
    M = 357.5291092 + 35999.0502909 * T
    Mp = 134.9633964 + 477198.8675055 * T
    F = 93.2720950 + 483202.0175233 * T
    Ec = 1 - 0.002516 * T
    lon = Lp.copy()
    for c, dd, m, mp, f in SL:
        lon = lon + c * Ec ** abs(m) * np.sin(rad(dd * D + m * M + mp * Mp + f * F)) / 1e6
    Ls = 280.46646 + 36000.76983 * T
    Ms = 357.52911 + 35999.05029 * T
    C = (1.914602 - 0.004817 * T) * np.sin(rad(Ms)) + 0.019993 * np.sin(rad(2 * Ms))
    return (lon - (Ls + C)) % 360


def lday_check(W):
    """計算した旧暦日（朔を含む日が1日）と、日記の旧暦日の比べ。全期間の日（不明も含む）。"""
    ords = W["ords"]
    d0 = _ecl_lon_diff(jd_of(ords, 0))
    d1 = _ecl_lon_diff(jd_of(ords + 1, 0))
    new = d1 < d0                                     # 0度をまたぐ ＝ 朔の瞬間がその日の中にある
    full = (d0 < 180) & (d1 >= 180)                   # 180度をまたぐ ＝ 望の瞬間がその日の中にある
    calc = np.zeros(len(ords), int)
    cur = 0
    for i in range(len(ords)):
        cur = 1 if new[i] else cur + 1
        calc[i] = cur
    ok = calc > 0
    first_new = int(np.argmax(new))
    ld = W["ld"]
    diff = (calc - ld)
    diff = np.where(diff > 15, diff - 30, np.where(diff < -15, diff + 30, diff))
    s = slice(first_new, None)
    dist = {int(k): int(v) for k, v in zip(*np.unique(diff[s], return_counts=True))}
    fl = ld[full]
    fd = {int(k): int(v) for k, v in zip(*np.unique(fl, return_counts=True))}
    return dict(n=int(len(diff[s])), same=float(100 * (diff[s] == 0).mean()), diff_dist=dist, full_moon_lday=fd,
                full_n=int(full.sum()), full_15=float(100 * (fl == 15).mean()), full_16=float(100 * (fl == 16).mean()),
                full_14=float(100 * (fl == 14).mean()))


# ============================================================
# 照合
# ============================================================
def _scalar_moon(jd):
    """1つずつ書いた同じ式（research/edo_yomichi_calc/moon.py の moon_simple と同じ）。"""
    r = math.radians
    T = (jd - 2451545.0) / 36525
    Lp = 218.3164477 + 481267.88123421 * T
    D = 297.8501921 + 445267.1114034 * T
    M = 357.5291092 + 35999.0502909 * T
    Mp = 134.9633964 + 477198.8675055 * T
    F = 93.2720950 + 483202.0175233 * T
    E = 1 - 0.002516 * T
    lon = Lp
    for c, d, m, mp, f in SL:
        lon += c * E ** abs(m) * math.sin(r(d * D + m * M + mp * Mp + f * F)) / 1e6
    lat = 0.0
    for c, d, m, mp, f in SB:
        lat += c * math.sin(r(d * D + m * M + mp * Mp + f * F)) / 1e6
    dist = 385000.56
    for c, d, m, mp, f in SR:
        dist += c * math.cos(r(d * D + m * M + mp * Mp + f * F)) / 1000
    eps = r(23.4392911 - 0.0130042 * T)
    lam = r(lon % 360)
    beta = r(lat)
    ra = math.atan2(math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps), math.cos(lam))
    dec = math.asin(math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam))
    Ls = 280.46646 + 36000.76983 * T
    Ms = 357.52911 + 35999.05029 * T
    C = (1.914602 - 0.004817 * T) * math.sin(r(Ms)) + 0.019993 * math.sin(r(2 * Ms))
    sun_lon = (Ls + C) % 360
    el = math.degrees(math.acos(max(-1, min(1, math.cos(beta) * math.cos(lam - r(sun_lon))))))
    return ra, dec, dist, el


def _scalar_light(jd):
    ra, dec, dist, el = _scalar_moon(jd)
    T = (jd - 2451545.0) / 36525
    gmst = (280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T) % 360
    H = math.radians(gmst + LON) - ra
    la = math.radians(LAT)
    alt = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(H))
    alt -= math.asin(6378.14 / dist) * math.cos(alt)
    if alt <= 0:
        return 0.0
    alpha = 180 - el
    ph = 10 ** (-0.4 * (0.026 * alpha + 4e-9 * alpha ** 4))
    s = math.sin(alt)
    X = 1 / (s + 0.025 * math.exp(-11 * s))
    return 0.267 * (384400 / dist) ** 2 * ph * 10 ** (-0.4 * 0.20 * X) * s


def _ephem_light(ephem, o, mo, t_local_dt):
    """year.py と同じ式（ephem の月）。t_local_dt: 地方平均時の datetime。"""
    import datetime as dt
    off = dt.timedelta(hours=LOC_H)
    o.date = ephem.Date(t_local_dt - off)
    mo.compute(o)
    h = float(mo.alt)
    if h <= 0:
        return 0.0, h
    alpha = 180 - abs(math.degrees(float(mo.elong)))
    ph = 10 ** (-0.4 * (0.026 * alpha + 4e-9 * alpha ** 4))
    X = 1 / (math.sin(h) + 0.025 * math.exp(-11 * math.sin(h)))
    dist = mo.earth_distance * 149597870.7
    return 0.267 * (384400 / dist) ** 2 * ph * 10 ** (-0.4 * 0.20 * X) * math.sin(h), h


def run_checks(days, W, ex, H0, quiet=False):
    """戻り値: (結果のdict, すべて通ったか)。"""
    import datetime as dt
    res = {}
    allok = True

    def rec(name, ok, detail):
        nonlocal allok
        allok &= bool(ok)
        res[name] = dict(ok=bool(ok), detail=detail)
        if not quiet:
            print(("OK  " if ok else "NG  ") + name + " : " + detail)

    # 1. 日記の表
    n = len(W["rows"])
    cont = bool(np.all(np.diff(W["ords"]) == 1))
    ldseq = bool(np.all((W["ld"][1:] == W["ld"][:-1] + 1) | ((W["ld"][1:] == 1) & (W["ld"][:-1] >= 29))))
    rec("日記の表", cont and ldseq and n == 31875 and days.nd == 22050,
        f"{n}日（連続={cont}・旧暦日の並び={ldseq}）、天気が分かる日 {days.nd}日（不明を除く）")

    # 2. ベクトル版 ＝ スカラー版
    rng = np.random.default_rng(7)
    jd = 2371000 + rng.random(300) * 31000
    ev = moon_light(jd)[0]
    es = np.array([_scalar_light(float(x)) for x in jd])
    dmax = float(np.abs(ev - es).max())
    rec("簡易式 ベクトル版＝スカラー版", dmax < 1e-9, f"300点の照度の差の最大 {dmax:.2e} lx")

    # 3. 1人ずつ書いたスカラー版で200人
    P = walk_people(days, *draw(days, MAIN_SEED, 200))
    bad = 0
    for i in range(200):
        di = int(P["di"][i])
        t0 = days.dusk[di] + int(P["off"][i])
        cnt = 0
        for k in range(WALK):
            e = _scalar_light(float(jd_of(days.ords[di], t0 + k)))
            cnt += e >= LINE
        mine = int(P["nosky"][i])
        if cnt != mine:
            # 閾値すれすれの float32 と float64 の違いは許す（照度が線の ±1e-4 以内）
            near = abs(_scalar_light(float(jd_of(days.ords[di], t0))) - LINE) < 1e-3
            bad += 0 if near and abs(cnt - mine) <= 1 else 1
    rec("1人ずつ書いたスカラー版", bad == 0, f"200人の歩けた分（空を無視）が一致しない人 {bad}人")

    # 4. 厳密計算 ≒ 1万人
    worst_z = 0.0
    items = [("home", "帰れた割合"), ("lday13_home", "十三夜"), ("lday14_home", "十四夜"), ("lday15_home", "十五夜"),
             ("lday16_home", "十六夜"), ("season0_home", "冬"), ("season2_home", "夏")]
    parts = []
    for key, nm in items:
        p = ex[key] / 100
        if key == "home":
            nn = H0["n"]
        elif key.startswith("lday"):
            nn = H0[key.replace("_home", "_n")]
        else:
            nn = H0[key.replace("_home", "_n")]
        se = 100 * math.sqrt(max(p * (1 - p), 1e-9) / nn)
        z = abs(H0[key] - ex[key]) / se
        worst_z = max(worst_z, z)
        parts.append(f"{nm} {H0[key]:.1f}/{ex[key]:.1f}(z={z:.1f})")
    rec("1万人 ≒ 厳密計算", worst_z < 4.0, "；".join(parts))

    # 5. 国立天文台の月の出入り（東京 2026年10月）
    if NAO_CSV.exists():
        lat_n, lon_n = 35.65, 139.7333
        errs = {"rise": [], "set": []}
        with open(NAO_CSV, encoding="utf-8") as f:
            for r in csv.DictReader(f):
                D = dt.date(2026, 10, int(r["day"])).toordinal()
                evs = moon_events(D, lat_n, lon_n, 9.0, start=0, end=1440)
                for key, col in (("rise", "rise_jst"), ("set", "set_jst")):
                    v = r[col]
                    if "-" in v:
                        continue
                    h, m = v.split(":")
                    tn = int(h) * 60 + int(m)
                    near = [x for x, k in evs if k == key]
                    if near:
                        errs[key].append(min(near, key=lambda x: abs(x - tn)) - tn)
        mx = max(max(abs(x) for x in errs["rise"]), max(abs(x) for x in errs["set"]))
        rec("国立天文台 月の出入り(2026-10 東京)", mx <= 3.5,
            f"月の出 n={len(errs['rise'])} 平均{np.mean(errs['rise']):+.1f}分 最大{max(abs(x) for x in errs['rise']):.1f}分／"
            f"月の入 n={len(errs['set'])} 平均{np.mean(errs['set']):+.1f}分 最大{max(abs(x) for x in errs['set']):.1f}分（NAOの表は分単位）")
    else:
        rec("国立天文台 月の出入り", False, f"照合データがない: {NAO_CSV}")

    # 6. ephem（照合用）
    try:
        import ephem
    except ImportError:
        ephem = None
    if ephem is None:
        res["ephem照合"] = dict(ok=None, detail="ephem が見つからないので省略（PYTHONPATH に置くと照合する）")
        if not quiet:
            print("--  ephem照合 : ephem が見つからないので省略")
    else:
        o = ephem.Observer()
        o.lat, o.lon, o.pressure = str(LAT), str(LON), 0
        mo = ephem.Moon()
        sun = ephem.Sun()
        dates = [dt.date(1845, 10, 12), dt.date(1845, 10, 14), dt.date(1845, 10, 16), dt.date(1845, 1, 12), dt.date(1845, 1, 15),
                 dt.date(1845, 7, 13), dt.date(1845, 7, 15), dt.date(1845, 4, 12), dt.date(1845, 12, 14)]
        dE = []
        dsun = []
        for D in dates:
            ordv = np.array([D.toordinal()])
            dusk = float(solve_sun(ordv, False)[0])
            dawn = float(solve_sun(ordv + 1, True)[0]) + 1440
            yot = dusk + (dawn - dusk) * 2 / 6
            o2 = ephem.Observer()
            o2.lat, o2.lon, o2.pressure, o2.horizon = str(LAT), str(LON), 0, "-7:21:40"
            o2.date = ephem.Date(dt.datetime(D.year, D.month, D.day, 12) - dt.timedelta(hours=LOC_H))
            e_dusk = ephem.Date(o2.next_setting(sun, use_center=True)).datetime() + dt.timedelta(hours=LOC_H)
            e_dawn = ephem.Date(o2.next_rising(sun, use_center=True)).datetime() + dt.timedelta(hours=LOC_H)
            base = dt.datetime(D.year, D.month, D.day)
            ed = (e_dusk - base).total_seconds() / 60
            ew = (e_dawn - base).total_seconds() / 60
            ey = ed + (ew - ed) * 2 / 6
            dsun += [dusk - ed, yot - ey]
            for j in range(0, int(yot - dusk) + 1, 10):
                t = dusk + j
                e_mine = float(moon_light(jd_of(ordv, np.array([t])))[0][0])
                e_ref, _ = _ephem_light(ephem, o, mo, base + dt.timedelta(minutes=t))
                dE.append((e_mine, e_ref))
        dE = np.array(dE)
        absd = np.abs(dE[:, 0] - dE[:, 1])
        big = dE[:, 1] >= 0.02
        rel = (absd[big] / dE[big, 1]) if big.any() else np.array([0.0])
        flip = int(((dE[:, 0] >= LINE) != (dE[:, 1] >= LINE)).sum())
        ok = float(absd.max()) < 0.01 and float(rel.max()) < 0.06 and float(np.abs(dsun).max()) < 1.5
        rec("ephem照合(1845年 9夜)", ok,
            f"照度の差 最大{absd.max():.4f} lx・0.02 lx 以上の点の相対差 最大{100 * rel.max():.1f}%（{int(big.sum())}点）・"
            f"線(0.05 lx)をまたぐ向きが違う点 {flip}/{len(dE)}・暮六つ/夜四つの差 最大{np.abs(dsun).max():.2f}分")
    # 7. 旧暦日 と 満月の瞬間
    LC = lday_check(W)
    res["旧暦日の比べ(参考)"] = dict(ok=None, detail=LC)
    if not quiet:
        print(f"--  旧暦日(参考): 計算（新月の日が1日）と日記が同じ {LC['same']:.1f}%、ずれ {LC['diff_dist']}")
        print(f"--  満月の瞬間が来る日記の旧暦日: 14日 {LC['full_14']:.0f}%・15日 {LC['full_15']:.0f}%・16日 {LC['full_16']:.0f}%（n={LC['full_n']}）")
    return res, allok


# ============================================================
# 計算
# ============================================================
def compute():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    W = load_weather()
    days = Days(W)
    print(f"日記 {len(W['rows'])}日 → 天気が分かる日 {days.nd}日・格子 {days.E.shape}（{time.time() - t0:.0f}秒）")
    P0 = walk_people(days, *draw(days, MAIN_SEED))
    H0 = headline(days, P0)
    tab = exact_tables(days)
    EX = exact_summary(days, tab=tab)
    cards = pick_cards(days, P0)
    prof = moon_profile(days)

    # 幅
    wide = {}
    di, off, u = P0["di"], P0["off"], P0["u"]
    for nm, line, pc in (("line0.02", LINE_LOW, 1.0), ("clear-10%", LINE, CLEAR_CUT), ("line0.01", 0.01, 1.0), ("line0.1", 0.1, 1.0),
                         ("line0.02&clear-10%", LINE_LOW, CLEAR_CUT)):
        P = walk_people(days, di, off, u, line, pc)
        h = headline(days, P)
        e = exact_summary(days, line, pc)
        wide[nm] = dict(mc=h, exact={k: e[k] for k in ("home", "mins_mean", "mins_median", "zero")})
    # 頑健さ
    rob = []
    for sd in [MAIN_SEED] + ROB_SEEDS:
        d3, o3, u3 = draw(days, sd)
        h = headline(days, walk_people(days, d3, o3, u3))
        h2 = headline(days, walk_people(days, d3, o3, u3, LINE_LOW))["home"]
        h3 = headline(days, walk_people(days, d3, o3, u3, LINE, CLEAR_CUT))["home"]
        rob.append(dict(seed=sd, home=h["home"], mins_mean=h["mins_mean"], mins_median=h["mins_median"],
                        lday13=h["lday13_home"], lday14=h["lday14_home"], lday15=h["lday15_home"], lday16=h["lday16_home"],
                        winter=h["season0_home"], summer=h["season2_home"], ratio=h["winter_over_summer"],
                        line002=h2, clear90=h3,
                        walk13=h["lday13_walk"], walk14=h["lday14_walk"], walk15=h["lday15_walk"], walk16=h["lday16_walk"]))
    checks, ok = run_checks(days, W, EX, H0)

    data = dict(
        slug=SLUG, made=time.strftime("%Y-%m-%d %H:%M"), n=N, main_seed=MAIN_SEED, rob_seeds=ROB_SEEDS, walk_min=WALK, line_lx=LINE,
        place=dict(lat=LAT, lon=LON), eligible_days=days.nd, diary_days=len(W["rows"]),
        diary_share={CLASSES[k]: float(100 * (days.day_cls == k).mean()) for k in range(5)},
        final_share={CLASSES[k]: float(100 * (days.cls == k).mean()) for k in range(5)},
        night_desc_days=int((days.night_cls >= 0).sum()), night_desc_share=float(100 * (days.night_cls >= 0).mean()),
        dusk_range=[clock(days.dusk.min()), clock(days.dusk.max())], yotsu_range=[clock(days.yotsu.min()), clock(days.yotsu.max())],
        window_min_range=[float((days.yotsu - days.dusk).min()), float((days.yotsu - days.dusk).max())],
        mc=H0, exact=EX, moon_profile=prof, cards=cards, wide=wide, robustness=rob,
        checks=checks, checks_all_ok=bool(ok), seconds=round(time.time() - t0, 1))
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


def write_numbers(D):
    mc, ex, cards = D["mc"], D["exact"], D["cards"]
    n = D["n"]
    se = lambda p, m: 100 * math.sqrt(max(p / 100 * (1 - p / 100), 0) / m)
    L = []
    a = L.append
    a(f"# 江戸の夜道 — 数字（{D['made']} 作成）")
    a("")
    a(f"1万人（種 {D['main_seed']}）。くじの対象の日: 日記 {D['diary_days']}日のうち天気が分かる {D['eligible_days']}日。"
      f"夜の記述がある日 {D['night_desc_days']}日（{pc(D['night_desc_share'])}）。")
    a(f"暮六つの範囲 {D['dusk_range'][0]}〜{D['dusk_range'][1]}、夜四つ {D['yotsu_range'][0]}〜{D['yotsu_range'][1]}（地方平均時）。")
    a(f"暮六つ〜夜四つの長さ {D['window_min_range'][0]:.0f}〜{D['window_min_range'][1]:.0f}分（出る時刻の幅はこれから60分引く）。")
    a("")
    a("## 日記の空（くじの対象日、%）")
    a("| | " + " | ".join(["晴", "陰晴", "曇", "雨雪", "雨止"]) + " |")
    a("|---|" + "---|" * 5)
    a("| 日の最後の天気 | " + " | ".join(f"{D['diary_share'][c]:.1f}" for c in ["晴", "陰晴", "曇", "雨雪", "雨止"]) + " |")
    a("| 夜の記述を優先した空 | " + " | ".join(f"{D['final_share'][c]:.1f}" for c in ["晴", "陰晴", "曇", "雨雪", "雨止"]) + " |")
    a("")
    a("## 全体（歩ける線 0.05 lx）")
    a(f"- **家まで帰れた: {mc['home']:.1f}%（100人に{mc['home']:.0f}人弱）** — 厳密計算 {ex['home']:.2f}%、標準誤差 ±{se(mc['home'], n):.2f}")
    a(f"- 月明かりで歩けた分: **中央値 {mc['mins_median']:.0f}分**、平均 {mc['mins_mean']:.1f}分（厳密: 中央値 {ex['mins_median']}分・平均 {ex['mins_mean']:.1f}分）")
    a(f"- 歩けた分が0の人: {mc['zero']:.1f}%（厳密 {ex['zero']:.1f}%）")
    a("")
    for key, title in (("worst", "いちばん悪かった人"), ("best", "いちばん良かった人")):
        c = cards[key]
        a(f"## {title}")
        if key == "worst":
            a(f"- 条件に合う人: **{cards['worst_n']}人**（歩けた分0・晦日ごろ(旧暦28日以降か1〜2日)・空が雨雪）。うち晦日そのもの {cards['worst_misoka_n']}人。"
              f"歩けた分0の人は全体で {cards['zero_n']}人。")
            a(f"- 代表の選び方: {cards['worst_rule']}")
        a(f"- {c['date']}（旧暦 {c['kyureki']}）・季節 {c['season']}")
        a(f"- 日記: 日の最後の天気={c['day_class']}・夜の記述={c['night_class'] or 'なし'} → 空={c['sky']}（この人は空が{'見える' if c['sky_visible'] else '見えない'}）")
        a(f"- 暮六つ {c['dusk']}・夜四つ {c['yotsu']}・出た時刻 {c['depart']}（暮六つの{c['depart_after_dusk_min']}分後）・着く時刻 {c['arrive']}（地方平均時）")
        ev = "、".join(f"{'月の出' if k == 'rise' else '月の入'} {t}" for t, k in c["moon_events"]) or "（昼12時〜翌昼12時に出入りなし）"
        a(f"- 月の出入り（その日の昼〜翌昼）: {ev}。月の光っている割合 {c['moon_lit_percent']:.0f}%")
        a(f"- 月の高度: 出るとき {c['moon_alt_at_depart']:.1f}°、着くとき {c['moon_alt_at_arrive']:.1f}°、60分の最大 {c['moon_alt_max_in_walk']:.1f}°")
        a(f"- 60分の照度: 平均 {c['E_mean']:.4f} lx・最大 {c['E_max']:.4f} lx（空を無視した値）。月明かりで歩けた分 {c['walkable_min']}分（空を無視すると {c['walkable_min_if_visible']}分）")
        a("")
    a("（良いほう次点）" + "；".join(
        f"{cards[k]['date']} 旧暦{cards[k]['kyureki']} {cards[k]['sky']} E平均{cards[k]['E_mean']:.3f} lx" for k in ("best_rank2", "best_rank3")))
    a("")
    a("## 問い2 旧暦日ごと（帰れた割合・歩けた分の割合）")
    a("歩けた分の割合 ＝ 歩けた分の合計 ÷（人数×60）。雲あり＝空のくじあり、雲なし＝空を無視。月の高さは暮六つ〜夜四つ（月が出ていない分は0）。")
    a("| 旧暦日 | 人数 | 帰れた(1万人) | 帰れた(厳密) | 歩けた分 雲あり | 歩けた分 雲なし(1万人) | 歩けた分 雲なし(厳密) | 暮六つの月の高さ | 窓の平均の月の高さ | 窓の平均照度 |")
    a("|---|---|---|---|---|---|---|---|---|---|")
    mp = D["moon_profile"]["by_lday"]
    for Ld in range(1, 31):
        p = mp.get(str(Ld))
        a(f"| {Ld} | {mc[f'lday{Ld}_n']} | {mc[f'lday{Ld}_home']:.1f}% | {ex[f'lday{Ld}_home']:.1f}% | {mc[f'lday{Ld}_walk']:.1f}% | "
          f"{mc[f'lday{Ld}_walk_nocloud']:.1f}% | {ex[f'lday{Ld}_walk_nocloud']:.1f}% | "
          + (f"{p['alt_dusk']:.1f}° | {p['alt_mean']:.1f}° | {p['E_mean']:.3f} lx |" if p else "- | - | - |"))
    a("")
    a("### 十三夜・十四夜・十五夜・十六夜（件数つき）")
    a("標準誤差: 1万人は人数から、厳密は日記の日どうしのばらつきから（日記の日を標本と見たとき）。")
    a("| 旧暦日 | 日記の日数 | 1万人の人数 | 帰れた(1万人) ±SE | 帰れた(厳密) ±SE | 歩けた分 雲あり(厳密) ±SE | 歩けた分 雲なし(厳密) ±SE |")
    a("|---|---|---|---|---|---|---|")
    for Ld in (13, 14, 15, 16):
        a(f"| {Ld} | {ex[f'lday{Ld}_n']} | {mc[f'lday{Ld}_n']} | {mc[f'lday{Ld}_home']:.1f}% ±{se(mc[f'lday{Ld}_home'], mc[f'lday{Ld}_n']):.1f} | "
          f"{ex[f'lday{Ld}_home']:.1f}% ±{ex[f'lday{Ld}_home_se']:.1f} | {ex[f'lday{Ld}_walk']:.1f}% ±{ex[f'lday{Ld}_walk_se']:.1f} | "
          f"{ex[f'lday{Ld}_walk_nocloud']:.1f}% ±{ex[f'lday{Ld}_walk_nocloud_se']:.1f} |")
    for x in (13, 14):
        diff = mc[f"lday{x}_home"] - mc["lday15_home"]
        sed = math.hypot(se(mc[f"lday{x}_home"], mc[f"lday{x}_n"]), se(mc["lday15_home"], mc["lday15_n"]))
        dx = ex[f"lday{x}_home"] - ex["lday15_home"]
        sdx = math.hypot(ex[f"lday{x}_home_se"], ex["lday15_home_se"])
        wx = ex[f"lday{x}_walk_nocloud"] - ex["lday15_walk_nocloud"]
        swx = math.hypot(ex[f"lday{x}_walk_nocloud_se"], ex["lday15_walk_nocloud_se"])
        wc = ex[f"lday{x}_walk"] - ex["lday15_walk"]
        swc = math.hypot(ex[f"lday{x}_walk_se"], ex["lday15_walk_se"])
        a(f"- 旧暦{x}日 − 15日: 帰れた割合 1万人 {diff:+.1f}pt（±{sed:.1f}）／厳密 {dx:+.1f}pt（±{sdx:.1f}）。歩けた分 雲あり(厳密) {wc:+.1f}pt（±{swc:.1f}）、雲なし(厳密) {wx:+.1f}pt（±{swx:.1f}）")
    a("")
    a("## 問い3 季節ごと（新暦）")
    a("| 季節 | 人数 | 帰れた(1万人) ±SE | 帰れた(厳密) | 晴の日の割合(日記・日の最後) | 空が見える確率の平均 | 旧暦13〜16日の暮六つ〜夜四つの月の高さ(平均) | その間月が出ている時間 | 同・平均照度 |")
    a("|---|---|---|---|---|---|---|---|---|")
    for k in range(4):
        s = D["moon_profile"]["by_season"][str(k)]
        a(f"| {SEASONS[k]} | {mc[f'season{k}_n']} | {mc[f'season{k}_home']:.1f}% ±{se(mc[f'season{k}_home'], mc[f'season{k}_n']):.1f} | "
          f"{ex[f'season{k}_home']:.1f}% ±{ex[f'season{k}_home_se']:.1f} | {s['clear_day']:.1f}% | {s['vis_prob']:.1f}% | {s['alt_1316']:.1f}°（{s['n_1316']}日） | {s['up_1316']:.0f}% | {s['E_1316']:.3f} lx |")
    a(f"- **冬 ÷ 夏: 1万人 {mc['winter_over_summer']:.1f}倍、厳密 {ex['winter_over_summer']:.1f}倍**（冬 {mc['season0_home']:.1f}% / 夏 {mc['season2_home']:.1f}%）")
    a("")
    a("## 幅（画面の札に1回だけ）")
    w = D["wide"]
    a("| 変えたもの | 帰れた(1万人) | 帰れた(厳密) | 歩けた分 中央値(厳密) | 平均(厳密) |")
    a("|---|---|---|---|---|")
    names = {"line0.01": "線 0.01 lx", "line0.02": "線 0.02 lx", "clear-10%": "日記の晴れを1割減(晴の確率0.9)", "line0.1": "線 0.1 lx",
             "line0.02&clear-10%": "線 0.02 lx ＋ 晴れ1割減"}
    a(f"| 基準（線 0.05 lx・日記のまま） | {mc['home']:.1f}% | {ex['home']:.1f}% | {ex['mins_median']}分 | {ex['mins_mean']:.1f}分 |")
    for k in ("line0.01", "line0.02", "line0.1", "clear-10%", "line0.02&clear-10%"):
        a(f"| {names[k]} | {w[k]['mc']['home']:.1f}% | {w[k]['exact']['home']:.1f}% | {w[k]['exact']['mins_median']}分 | {w[k]['exact']['mins_mean']:.1f}分 |")
    a("")
    a("## 頑健さ（種を変えて1万人をやり直し）")
    a("| 種 | 帰れた | 歩けた分 中央値 | 平均 | 十三夜 | 十四夜 | 十五夜 | 十六夜 | 冬 | 夏 | 冬/夏 | 線0.02 | 晴1割減 |")
    a("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in D["robustness"]:
        a(f"| {r['seed']} | {r['home']:.1f}% | {r['mins_median']:.0f} | {r['mins_mean']:.1f} | {r['lday13']:.1f}% | {r['lday14']:.1f}% | {r['lday15']:.1f}% | "
          f"{r['lday16']:.1f}% | {r['winter']:.1f}% | {r['summer']:.1f}% | {r['ratio']:.1f} | {r['line002']:.1f}% | {r['clear90']:.1f}% |")
    keys = [("home", "帰れた"), ("mins_mean", "歩けた分 平均"), ("lday13", "十三夜"), ("lday14", "十四夜"), ("lday15", "十五夜"), ("lday16", "十六夜"),
            ("winter", "冬"), ("summer", "夏"), ("ratio", "冬/夏"), ("line002", "線0.02"), ("clear90", "晴1割減")]
    a("")
    a("6回（主＋5）の最小〜最大 / 標準偏差")
    for kx, nm in keys:
        v = np.array([r[kx] for r in D["robustness"]])
        a(f"- {nm}: {v.min():.1f}〜{v.max():.1f}（標準偏差 {v.std(ddof=1):.2f}）")
    a("- 十三夜・十四夜が十五夜より上: " + "、".join(
        f"種{r['seed']}: 13>15 {'○' if r['lday13'] > r['lday15'] else '×'} 14>15 {'○' if r['lday14'] > r['lday15'] else '×'}" for r in D["robustness"]))
    a("")
    a("## 照合")
    for nm, c in D["checks"].items():
        mark = "OK" if c["ok"] else ("--" if c["ok"] is None else "NG")
        det = c["detail"]
        if isinstance(det, dict):
            det = f"計算と日記の旧暦日が同じ {det['same']:.1f}%、ずれ(計算−日記) {det['diff_dist']}。満月の瞬間: 14日 {det['full_14']:.0f}%・15日 {det['full_15']:.0f}%・16日 {det['full_16']:.0f}%（n={det['full_n']}）"
        a(f"- {mark} {nm}: {det}")
    a("")
    a("## 仮定（札に出す）")
    a("- 歩ける線 0.05 lx（ふつうの満月くらい）／ 空は日記の「その日の最後の天気」か夜の記述で代用（日記は晴れが多めに出る傾向）")
    a("- 出る時刻は暮六つ〜夜四つ−60分から一様／ 道は1里＝60分／ 月が建物に隠れる高さは考えない／ 旧暦日は日記の日付")
    (OUT / "numbers.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("書き出し:", OUT / "numbers.md")


# ============================================================
# 場面で使う1人ぶんのデータ（同じ1万人・同じモデル関数から取り出すだけ。data.json・数字は変えない）
# ============================================================
SCENE_JSON = OUT / "scene_people.json"


def scene_data(force=False):
    """場面に出す町人（九夜・十五夜・十六夜・冬・梅雨）の60分の照度と月の高さ、月の出の時刻、帯の月の高さなど。
    1万人（種 MAIN_SEED）の中から条件に合う人を選ぶ（選び方は各行のコメント）。梅雨の人だけ、日記の1日（1788-06-17）を指定して模型で計算。"""
    if SCENE_JSON.exists() and not force:
        _old = json.loads(SCENE_JSON.read_text(encoding="utf-8"))
        if "summer" in _old.get("people", {}):
            return _old
    import datetime as dt
    t0 = time.time()
    W = load_weather()
    days = Days(W)
    P = walk_people(days, *draw(days, MAIN_SEED))
    di = P["di"]
    mid = np.abs((P["off"] + 0.5) / days.noff[di] - 0.5)
    ld, cls, vis, mins, E60 = days.ld[di], days.cls[di], P["vis"], P["mins"], P["E60"]

    def pick(mask, key=None):
        idx = np.nonzero(mask)[0]
        if len(idx) == 0:
            raise SystemExit("scene_data: 条件に合う人がいない")
        sc = mid[idx] if key is None else key[idx]
        return int(idx[np.argmin(sc)])

    out = dict(made=time.strftime("%Y-%m-%d %H:%M"), seed=MAIN_SEED, people={})
    # 九夜: 旧暦9日・晴・空が見える・歩けた分0（出る時刻が窓の真ん中に近い人）
    out["people"]["n9"] = person_card(days, P, pick((ld == 9) & (cls == 0) & vis & (mins == 0)))
    # 十五夜: 旧暦15日・晴・空が見える・家まで帰れた
    out["people"]["n15"] = person_card(days, P, pick((ld == 15) & (cls == 0) & vis & P["home"]))
    # 十六夜: 旧暦16日・晴・空が見える・前半は線の下・後半は線の上（歩けた分が30に近い人）
    cross = (E60[:, 0] < LINE) & (E60[:, -1] >= LINE)
    out["people"]["n16"] = person_card(days, P, pick((ld == 16) & (cls == 0) & vis & cross, np.abs(mins - 30) + mid))
    # 冬: 新暦12〜2月・旧暦14日・晴・家まで帰れた
    out["people"]["winter14"] = person_card(days, P, pick((days.season[di] == 0) & (ld == 14) & (cls == 0) & vis & P["home"]))
    # 梅雨: 1788-06-17（旧暦5月14日・日記は昼も夜も雨）。出る時刻は窓の真ん中
    ordv = dt.date(1788, 6, 17).toordinal()
    dj = int(np.nonzero(days.ords == ordv)[0][0])
    off = int(days.noff[dj] // 2)
    jd = jd_of(int(days.ords[dj]), days.dusk[dj] + off + np.arange(WALK))
    nosky = int((moon_light(jd)[0] >= LINE).sum())
    P1 = dict(di=np.array([dj]), off=np.array([off]), vis=np.array([False]), mins=np.array([0]), nosky=np.array([nosky]))
    out["people"]["tsuyu"] = person_card(days, P1, 0)
    # 夏の晴れの人: 新暦6〜8月・旧暦14〜15日・晴・空が見える・歩けた分0（出る時刻が窓の真ん中に近い人）。1万人の中から選ぶ
    out["people"]["summer"] = person_card(days, P, pick((days.season[di] == 2) & ((ld == 14) | (ld == 15)) & (cls == 0) & vis & (mins == 0)))
    # 月の出の時刻（旧暦日ごと・日記の日から最大25日の中央値。0時からの分。24時を過ぎたら 1440 を足した値）
    rise = {}
    for L in (15, 16, 17, 20, 23, 26, 29):
        sel = np.nonzero(days.ld == L)[0][::max(1, int((days.ld == L).sum() // 25))][:25]
        v = []
        for k in sel:
            ev = [x for x, kind in moon_events(int(days.ords[k])) if kind == "rise"]
            if ev:
                v.append(ev[0])
        rise[str(L)] = float(np.median(v))
    out["rise_by_lday"] = rise
    # 帰り道の窓（暮六つ〜夜四つ）の月の高さ（最悪の日・最良の日）
    win = {}
    for nm, d_ in (("best", "1833-01-06"), ("worst", "1836-05-14")):
        k = int(np.nonzero(days.ords == dt.date.fromisoformat(d_).toordinal())[0][0])
        m = np.arange(0, int(days.yotsu[k] - days.dusk[k]) + 1, 5.0)
        e, h, _ = moon_light(jd_of(int(days.ords[k]), days.dusk[k] + m))
        win[nm] = dict(date=d_, dusk=clock(days.dusk[k]), yotsu=clock(days.yotsu[k]), minutes=[float(x) for x in m],
                       alt=[r1(x) for x in h], E=[float(round(x, 5)) for x in e])
    out["window"] = win
    # 1万人を歩けた分の小さい順に並べたときの、分ごとの人数（0〜60）
    out["hist_mins"] = [int(x) for x in np.bincount(P["mins"], minlength=WALK + 1)]
    out["n"] = int(len(di))
    out["seconds"] = round(time.time() - t0, 1)
    SCENE_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=1, default=_js), encoding="utf-8")
    print("書き出し:", SCENE_JSON, f"（{time.time() - t0:.0f}秒）")
    return out


def main():
    args = sys.argv[1:]
    if "--compute" in args:
        compute()
        return
    if "--check" in args:
        W = load_weather()
        days = Days(W)
        P0 = walk_people(days, *draw(days, MAIN_SEED))
        _, ok = run_checks(days, W, exact_summary(days), headline(days, P0))
        print("照合:", "すべて通った" if ok else "通らないものがある")
        return
    if "--numbers" in args:
        p = OUT / "data.json"
        if not p.exists():
            raise SystemExit("data.json がありません（--compute で作る）")
        write_numbers(json.loads(p.read_text(encoding="utf-8")))
        return
    if "--scenedata" in args:
        scene_data(force=True)
        return
    print(__doc__)


_MODEL_CLI = any(a in sys.argv for a in ("--compute", "--check", "--numbers", "--scenedata"))
if __name__ == "__main__" and _MODEL_CLI:
    main()
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・声の並び・照合・静止画）。sims/chikyu-long.py・uchujin-long.py と同じ並び・同じ部品
# （見開きノート・付せん・章カード・終了画面・区切り lk.Eyecatch・照合・静止画）。
# 台本: publish/yomichi-long/narration_B.md の「## 0」より後の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 絵の方針: 見開きのノートの手描き風。夜の場面は紙の地に藍色をうすく塗る（画面全体は暗くしない）。空は窓（夜空の四角）に入れる。
#   町人は画面の高さの4割以上（棒人間＋着物）。1人に寄る場面は 町人・空の月（満ち欠けと高さ）・右下の「明るさ」の目盛りと「歩ける線」・1時間の帯。
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
import edo_people  # noqa: E402  町人の絵（2026-10-28）

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


# ============================================================
# 小さな道具（chikyu-long・uchujin-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"                                     # 歩けた
GOLD = "#f2c14e"                                     # 月の光
DIM = "#b9bdcc"                                      # 歩けなかった（灰）
NAVY = "#1c2a5a"                                     # 夜の藍
SKY_D0, SKY_D1 = "#0b1438", "#273a78"                # 夜空の窓


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
    """余白の小さい付箋。(x, y) は中心（align='left' なら左端）。戻り値は (幅, 高さ)"""
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


def cross_mark(ctx, cx, cy, r, a=1.0, p=1.0):
    """赤ペンの×（外れの印）"""
    if p <= 0:
        return
    pen_line(ctx, cx - r, cy - r, cx + r, cy + r, RED, seed=31, width=11, progress=clamp01(p * 2), alpha=a)
    if p > 0.5:
        pen_line(ctx, cx + r, cy - r, cx - r, cy + r, RED, seed=33, width=11, progress=clamp01(p * 2 - 1), alpha=a)


# ============================================================
# 準備（データ・時間割）
# ============================================================
lf.use()
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
SD = scene_data()
_syn = _fake_synth if FAKE else _voice_synth
_ITEMS = _breathe(_items())                    # 台本の並び（場面の切りかえの間は、ID が決まってから _pace で足す）

CARD_BY_N = {1: "悪い夜と良い夜は？", 2: "満月なら、帰れる？", 3: "冬と夏、どちらが？", 4: "まとめ"}
CH_TITLES = [c["title"] for c in CHAPS]
CARD_TITLES = [CARD_BY_N.get(c["n"], c["title"]) for c in CHAPS]


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ---- 場面の合図: 文の一部（手がかり）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    # 0 冒頭
    "c0_q": (0, "家まで帰れるでしょうか"), "c0_lan": (0, "火をともして"), "c0_forgot": (0, "は、ありません"), 
    "c0_drew": (0, "月は、半分ほど"), "c0_left": (0, "友だちの家を出ます"), "c0_dark": (0, "歩ける明るさに届きません"), "c0_10k": (0, "でためしました"),
    "c0_res": (0, "ほどでした"), "c0_cond": (0, "に書いてあります"), "c0_assume": (0, "仮に置いた条件です"), "c0_next": (0, "順に確かめます"),
    "c0_q1": (0, "いちばん悪い夜と、いちばん良い夜は、どんな夜"), "c0_q2": (0, "満月のころの夜なら、だれでも"), "c0_q3": (0, "冬と夏では、どちらが帰りやすい"),
    # 1 いちばん悪い夜と、いちばん良い夜
    "c1_intro": (1, "最初の問いです"), "c1_yoso": (1, "まず、予想です"), "c1_yoso2": (1, "と思えます"), "c1_moon": (1, "月明かりとは"),
    "c1_kuji": (1, "くじのしかたを"), "c1_diary": (1, "毎日つけられていた日記から"), "c1_weather": (1, "天気は、日記のとおり"), "c1_time": (1, "出かける時刻は"), 
    "c1_cal": (1, "月の満ち欠けは"), "c1_kyu": (1, "旧暦と呼びます"), "c1_new": (1, "月のない夜です"), "c1_full": (1, "15日ごろに、満月"), "c1_wane": (1, "また欠けて"),
    "c1_line": (1, "暗めの明るさと"), "c1_gauge": (1, "月明かりの強さです"), "c1_gline": (1, "横の線が"), "c1_band": (1, "1時間のうち"), "c1_home": (1, "帰れた人と数えます"), "c1_med": (1, "ちょうど真ん中の"),
    "c1_med0": (1, "中央値は、0分"), "c1_9of10": (1, "10人に9人は"), "c1_wrong": (1, "予想の後半は、外れました"), "c1_dark": (1, "たいてい暗いのです"),
    "c1_wintro": (1, "いちばん暗かった夜を"), "c1_w29": (1, "29日の夜に出た人"), "c1_wrain": (1, "この日は雨でした"), "c1_east": (1, "東から昇って"),
    "c1_sun": (1, "太陽のすぐそば"), "c1_none": (1, "夜の空には、いません"), "c1_late": (1, "毎日、遅れていきます"), "c1_dawn": (1, "夜明け前にしか"),
    "c1_4h": (1, "4時半ごろまで"), "c1_wall": (1, "壁に手をつきながら"), "c1_1h": (1, "およそ1時間の道のり"), "c1_step": (1, "1歩目から"),
    "c1_w0": (1, "歩けた時間は、0分でした"), "c1_260": (1, "260人ほど"), "c1_nolone": (1, "不運では"),
    "c1_bintro": (1, "いちばん良かった人です"), "c1_bwinter": (1, "冬の、満月のころの"), "c1_bround": (1, "ほとんど丸い形"), "c1_bclear": (1, "すっかり晴れています"),
    "c1_bshadow": (1, "影が、道に長くのびて"), "c1_bhigh": (1, "明るく光っていました"), "c1_bline": (1, "「歩ける線」の上にありました"), "c1_bhour": (1, "1時間まるごと"),
    "c1_why": (1, "なぜ、これほど差が出る"), "c1_reason": (1, "空にあるかどうか"), "c1_month": (1, "10夜に4夜ほど"), "c1_8": (1, "およそ8日間は"), "c1_fewer": (1, "もっと少ないのです"), "c1_ans": (1, "答えです"),
    # 2 満月のころ
    "c2_intro": (2, "次の問いです"), "c2_yoso": (2, "予想です"), "c2_bright": (2, "いちばん明るい夜だから"), "c2_15": (2, "毎月の15日の夜を"), "c2_16": (2, "16日の夜は"),
    "c2_lim": (2, "満月とは限りません"), "c2_both": (2, "どちらも、満月のころ"), "c2_tiles": (2, "300人あまり"), "c2_frame": (2, "日にちごとに見てみます"),
    "c2_zero": (2, "ひとりもいません"), "c2_rise": (2, "少しずつ出はじめます"), "c2_15v": (2, "十五夜に出かけた人"), "c2_14v": (2, "ほぼ同じです"),
    "c2_44": (2, "10人に4人ほどなのです"), "c2_16v": (2, "10人に2人まで落ちます"), "c2_half": (2, "半分に落ちました"), "c2_winter": (2, "帰れた人がいます"),
    "c2_best": (2, "冬の十六夜でした"), "c2_17": (2, "になると、100人に4人"), "c2_after": (2, "ほとんど帰れません"), "c2_wrong": (2, "予想は、外れました"),
    "c2_look": (2, "明るく見えるのは"), "c2_other": (2, "別の話です"), "c2_pair": (2, "歩かせます"), "c2_p15": (2, "家まで歩ききりました"), "c2_p16": (2, "前半を暗い道で"),
    "c2_why": (2, "なぜでしょうか"), "c2_r1": (2, "理由の1つ目は、雲"), "c2_thick": (2, "厚い雲があれば"), "c2_half2": (2, "晴れの日は、およそ半分"),
    "c2_cloud": (2, "歩ける線の下にもどります"), "c2_r2": (2, "理由の2つ目は"), "c2_daily": (2, "少しずつ遅れて昇ります"), "c2_later": (2, "昇る時刻が遅い夜"),
    "c2_both2": (2, "夜もあります"), "c2_low": (2, "東の低いところ"), "c2_weak": (2, "光が弱いのです"), "c2_first": (2, "前半が、暗いのです"),
    "c2_dep": (2, "雲と月の出方しだい"), "c2_ans": (2, "帰れない人のほうが多い"),
    # 3 冬と夏
    "c3_intro": (3, "最後の問いです"), "c3_yoso": (3, "予想です"), "c3_cal": (3, "今のカレンダー"), "c3_2500": (3, "2500人ほど"), "c3_w": (3, "100人に10人ほど"),
    "c3_s": (3, "夏は、100人に2人"), "c3_5": (3, "夏の5倍"), "c3_sa": (3, "100人に9人ほど"), "c3_most": (3, "冬がいちばん多く"), "c3_wrong": (3, "予想は、外れました"),
    "c3_see": (3, "1人ずつ、見にいきます"), "c3_r1": (3, "理由の1つ目は、晴れ"), "c3_w7": (3, "10日に7日ほど"), "c3_s4": (3, "10日に4日ほど"), "c3_rainy": (3, "雨の続く梅雨"),
    "c3_rain2": (3, "空が見えません"), "c3_tsu": (3, "雲の下にいます"), "c3_r2": (3, "理由の2つ目は"), "c3_opp": (3, "太陽と反対がわ"), "c3_wlow": (3, "冬は、太陽が低い"),
    "c3_shigh": (3, "夏は、太陽が高い"), "c3_whigh": (3, "冬の満月は"), "c3_slow": (3, "夏の満月は"), "c3_41": (3, "冬が平均41度"), "c3_24": (3, "夏は、24度"),
    "c3_weak": (3, "地面を照らす光"), "c3_avg": (3, "平均してみます"), "c3_wline": (3, "冬は、歩ける線を超えます"), "c3_sline": (3, "夏は、歩ける線に"),
    "c3_between": (3, "線を少し超えます"), "c3_tsu2": (3, "雲がないのに、月が低く"), "c3_w2": (3, "影を落として"), "c3_diff": (3, "季節で、これほど差が出る"), "c3_ans": (3, "答えは、冬です"),
    # 4 まとめ
    "c4_0": (4, "ほどでした"), "c4_1": (4, "冬の晴れた夜です"), "c4_2": (4, "なしで、出かけますか"), "c4_3": (4, "町と条件で計算した"), "c4_sub": (4, "チャンネル登録と高評価"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    if len(hits) != 1:
        raise SystemExit(f"台本の手がかり「{sub}」が 第{n}章で {len(hits)} 件（1件だけのはず）。narration_B.md が変わったら ANCH を直してください")
    return hits[0]


ID = {k: _find(*v) for k, v in ANCH.items()}

# ---- 場面の切りかえの間（2026-10-29 ユーザー指摘「映像の切り替わりが早すぎる」）----
#   場面は、その場面で話している文の終わりまで消さない。次の場面は、その最初の文の頭の 1.05秒前（＝前の文の終わり）に出す。
#   そのため、第1章からは、場面の切りかえの前の文のあとの間を SCENE_GAP 秒以上にする（声の文は変えない。間だけ）。
#   冒頭（第0章）は間を足さない（結果の数字を30秒以内に言うため。0章の間は 0.3秒のまま）→ 0章の場面は前の文の終わりで切りかえる。
SCENE_GAP = 1.05
SCENE_KEYS = ["c1_moon", "c1_kuji", "c1_cal", "c1_line", "c1_med", "c1_wintro", "c1_260", "c1_bintro", "c1_why", "c1_reason", "c1_month", "c1_ans",
              "c2_15", "c2_tiles", "c2_look", "c2_pair", "c2_r1", "c2_half2", "c2_cloud", "c2_r2", "c2_low", "c2_first", "c2_ans",
              "c3_cal", "c3_see", "c3_w7", "c3_rainy", "c3_r2", "c3_wlow", "c3_avg", "c3_tsu2", "c4_1", "c4_2"]
# 文のあとの間を、札・図を読みきれる長さまでのばす（手がかり: 秒）。札は「文字数÷8＋1秒」以上出す
HOLD_AFTER = {
    "c2_both": 1.3,        # 「どちらも、満月のころの夜」の札（2.5秒）を読みきってから棒グラフへ
    "c2_wrong": 1.6,       # 「予想」の札に×がついてから読める間（2.0秒以上）
    "c3_wrong": 1.6,       # 同じ
    "c3_s4": 1.7,          # 夏の10個の丸が出そろってから見る間
}


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


_ITEMS = _pace(_ITEMS)
tl = lf.Timeline(_ITEMS, VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration
_LINE_ORDER = [it.id for it in tl.items if isinstance(it, lf.Line)]
PREV_LINE = {b: a for a, b in zip(_LINE_ORDER, _LINE_ORDER[1:])}


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
T_ES = Sk("c4_sub") - 0.3                                  # 終了画面の始まり（登録のお願いの文の頭の少し前から。問い・注意書き・札は、その前に読める）

# ---- データ（data.json と scene_people.json から。数字は data.json の値を四捨五入）----
MC = RES["mc"]
P_ALL = ihalf(MC["home"])                                 # 100人に7人
N_ALL = ihalf(MC["home"] * N / 100)                       # 1万人のうち 679人
LDAY_P = {L: MC[f"lday{L}_home"] for L in range(1, 31)}     # 旧暦日ごとの帰れた割合（%）
SEASON_P = [MC[f"season{k}_home"] for k in range(4)]        # 冬・春・夏・秋（%）
SEASON_E = [RES["moon_profile"]["by_season"][str(k)]["E_1316"] for k in range(4)]     # 旧暦13〜16日の窓の平均照度（lx）
SEASON_ALT = [RES["moon_profile"]["by_season"][str(k)]["alt_1316"] for k in range(4)]
SEASON_WIN = [RES["moon_profile"]["by_season"][str(k)]["window_min"] for k in range(4)]
CARDS_ = RES["cards"]
WORST, BEST = CARDS_["worst"], CARDS_["best"]
WORST_N = CARDS_["worst_n"]
UP_SHARE = {int(k): v["up_share"] for k, v in RES["moon_profile"]["by_lday"].items()}
ALT_DUSK = {int(k): v["alt_dusk"] for k, v in RES["moon_profile"]["by_lday"].items()}
HIST = SD["hist_mins"]                                     # 0〜60分ごとの人数
N_ZERO, N_HOME = HIST[0], HIST[WALK]
N_MID = N - N_ZERO - N_HOME
WIDE_P = ihalf(RES["wide"]["line0.02"]["mc"]["home"])      # 線を 0.02 lx にすると 100人に14人


# ============================================================
# 絵の部品（月・町人・提灯・くじ箱・空の窓・通り）。棒人間＋着物の手描き風
# ============================================================
SKIN, HAIR, OBI = "#f1cfa8", "#2a2a38", "#c98a3c"


def _poly(ctx, pts, close=True):
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    if close:
        ctx.close_path()


def glow(ctx, cx, cy, r, col=GOLD, a=0.5):
    """やわらかい光（放射状）"""
    if a <= 0.003:
        return
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    c = hexrgb(col)
    g.add_color_stop_rgba(0, c[0], c[1], c[2], a)
    g.add_color_stop_rgba(0.45, c[0], c[1], c[2], a * 0.35)
    g.add_color_stop_rgba(1, c[0], c[1], c[2], 0)
    ctx.set_source(g)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()


def moon_disc(ctx, cx, cy, r, lit, waxing=True, a=1.0, halo=0.0, dark_col="#46507a", dark_a=0.6, lit_col="#fff0a8", edge=None):
    """満ち欠けのある月。lit=光っている割合 0〜1。waxing=True なら右が光る（北半球の満ちていく月）。
    端の線は edge（色）。lit=0 は暗い円だけ（新月・月のない夜）"""
    if a <= 0.003:
        return
    if halo > 0:
        glow(ctx, cx, cy, r * 3.2, GOLD, halo * a * (0.35 + 0.65 * lit))
    ctx.set_source_rgba(*hexrgb(dark_col, dark_a * a))
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    if lit > 0.01:
        k = 1 - 2 * lit
        sgn = 1 if waxing else -1
        pts = []
        for i in range(41):
            th = -math.pi / 2 + math.pi * i / 40
            pts.append((cx + r * math.cos(th) * sgn, cy + r * math.sin(th)))
        for i in range(41):
            th = math.pi / 2 - math.pi * i / 40
            pts.append((cx + k * r * math.cos(th) * sgn, cy + r * math.sin(th)))
        _poly(ctx, pts)
        ctx.set_source_rgba(*hexrgb(lit_col, a))
        ctx.fill()
    if edge:
        ctx.set_source_rgba(*hexrgb(edge, 0.9 * a))
        ctx.set_line_width(max(2.0, r * 0.05))
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.stroke()


def lit_of_lday(L, add=0.3):
    """旧暦 L 日の夕方の月の光っている割合（新月から L-1+add 日）"""
    return (1 - math.cos(2 * math.pi * (L - 1 + add) / 29.53)) / 2


def sun_disc(ctx, cx, cy, r, a=1.0, rays=True):
    glow(ctx, cx, cy, r * 3, "#ffb347", 0.35 * a)
    ctx.set_source_rgba(*hexrgb("#ff9f2e", a))
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    if rays:
        ctx.set_source_rgba(*hexrgb("#ff9f2e", a))
        ctx.set_line_width(max(3.0, r * 0.16))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for k in range(12):
            an = k * math.pi / 6
            ctx.move_to(cx + r * 1.3 * math.cos(an), cy + r * 1.3 * math.sin(an))
            ctx.line_to(cx + r * 1.7 * math.cos(an), cy + r * 1.7 * math.sin(an))
        ctx.stroke()


def cloud(ctx, cx, cy, w, col="#c9cfdd", a=1.0):
    """もこもこの雲（幅 w）"""
    if a <= 0.003:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    for dx, dy, rr in ((-0.30, 0.05, 0.20), (-0.10, -0.08, 0.26), (0.14, -0.03, 0.23), (0.32, 0.06, 0.17), (0.0, 0.10, 0.28)):
        ctx.arc(cx + dx * w, cy + dy * w, rr * w * 0.62, 0, 2 * math.pi)
        ctx.fill()


_STARS = np.random.default_rng(7).random((90, 4))


def sky_window(ctx, x0, y0, x1, y1, t, kind="night", clouds=0.0, rain=False, a=1.0, roofs=True, stars=True, seed=0):
    """空の窓（角丸の四角）。kind='night'（藍）/'dark'（ほぼ真っ黒の闇夜）/'day'（昼の空）。clouds=0〜1 の雲の濃さ。屋根の影つき。
    窓の中は clip する。戻り値は地平線の y"""
    horizon = y1 - 22
    ctx.save()
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
    ctx.clip()
    g = cairo.LinearGradient(0, y0, 0, y1)
    c0, c1 = {"night": (SKY_D0, SKY_D1), "dark": ("#04071a", "#12183a"), "day": ("#7fb2e6", "#d3e9f8")}[kind]
    g.add_color_stop_rgba(0, *hexrgb(c0, a))
    g.add_color_stop_rgba(1, *hexrgb(c1, a))
    ctx.set_source(g)
    ctx.paint()
    if stars and kind != "day":
        n = 90 if kind == "night" else 30
        for i in range(n):
            sx, sy, ss, sp = _STARS[i]
            tw = 0.6 + 0.4 * math.sin(t * (1.2 + sp * 2.2) + sp * 40)
            ctx.set_source_rgba(1, 1, 0.92, (0.35 + 0.6 * ss) * tw * a * (1 - 0.8 * clouds))
            ctx.arc(x0 + 10 + sx * (x1 - x0 - 20), y0 + 8 + sy * (horizon - y0 - 30), 0.8 + 1.8 * ss, 0, 2 * math.pi)
            ctx.fill()
    if clouds > 0.003:
        n_c = 6
        for i in range(n_c):
            cx = x0 + ((i + 0.5) / n_c) * (x1 - x0) + 40 * math.sin(t * 0.25 + i * 1.7) + (i % 2) * 20
            cy = y0 + 55 + (i % 3) * 52 + 8 * math.sin(t * 0.4 + i)
            cloud(ctx, cx, cy, (x1 - x0) * 0.42, "#7b839c" if kind != "day" else "#cfd6e2", clouds * a * 0.95)
    if roofs:
        ctx.set_source_rgba(*hexrgb("#060b22", 0.94 * a))
        pts = [(x0 - 5, y1 + 5), (x0 - 5, horizon + 8)]
        rng = np.random.default_rng(3 + seed)
        xx = x0 - 5
        while xx < x1 + 10:
            wdt = rng.uniform(70, 150)
            hh = rng.uniform(4, 20)
            pts += [(xx, horizon + 8 - hh), (xx + wdt * 0.5, horizon - hh - 12), (xx + wdt, horizon + 8 - hh)]
            xx += wdt
        pts += [(x1 + 10, horizon + 8), (x1 + 10, y1 + 5)]
        _poly(ctx, pts)
        ctx.fill()
    if rain:
        ctx.set_source_rgba(0.82, 0.88, 1.0, 0.5 * a)
        ctx.set_line_width(2.2)
        for i in range(46):
            rx = (i * 97.0 + t * 260) % (x1 - x0 + 160) + x0 - 80
            ry = ((i * 53.0) % (y1 - y0) + t * 520) % (y1 - y0) + y0
            ctx.move_to(rx, ry)
            ctx.line_to(rx - 9, ry + 26)
        ctx.stroke()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(3.5)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
    ctx.stroke()
    return horizon


# ---- 町人 ----
def person(ctx, cx, fy, h, t=0.0, pose="stand", face=1, umbrella=False, kimono="#4d6fb3", a=1.0, step=True, lookup=False, night=False):
    """町人（2026-10-28 描き直し: sims/edo_people.py の横向きの町人）。(cx, fy)=足もと中央、h=身長、face=+1 右向き。
    pose: 'stand' 立つ／'walk' 歩く（t で足が動く）／'wall' 手さぐり（片手を前へ、柱をさぐる）。umbrella=傘をさす"""
    if a <= 0.003:
        return
    u = h / 100.0
    if pose == "wall":
        ctx.save()                                                             # さぐる先の柱
        ctx.translate(cx, fy)
        ctx.scale(face, 1)
        ctx.set_source_rgba(*hexrgb("#6b4f33", a))
        ctx.rectangle(37.0 * u, -108 * u, 5.5 * u, 108 * u)
        ctx.fill()
        ctx.restore()
    pz = {"walk": t * 7.0 / (2 * math.pi), "wall": t * 3.0 / (2 * math.pi)}.get(pose, 0.0)
    edo_people.draw_townsman(ctx, cx, fy, h, pose={"wall": "grope"}.get(pose, pose), phase=pz % 1.0, facing=face,
                             kimono=kimono, a=a, night=night, hold=umbrella, lookup=lookup)
    if umbrella:
        ctx.save()
        ctx.translate(cx, fy)
        ctx.scale(face, 1)
        ux, uy = edo_people.HOLD_HAND[0] * u, edo_people.HOLD_HAND[1] * u
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(1.3 * u)
        ctx.move_to(ux, uy + 4 * u)
        ctx.line_to(ux, -122 * u)
        ctx.stroke()
        ctx.save()
        ctx.translate(ux, -122 * u)
        ctx.scale(1.0, 0.5)
        ctx.arc(0, 0, 32 * u, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#b8433a", a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(1.5 * u)
        ctx.stroke()
        for k in range(-2, 3):
            ctx.move_to(ux, -122 * u)
            ctx.line_to(ux + k * 12.8 * u, -122 * u - (16 * u) * math.sqrt(max(0.0, 1 - (k / 2.5) ** 2)))
        ctx.set_source_rgba(*hexrgb("#f4ead6", a * 0.8))
        ctx.set_line_width(1.0 * u)
        ctx.stroke()
        ctx.restore()


def person_old(ctx, cx, fy, h, t=0.0, pose="stand", face=1, umbrella=False, kimono="#4d6fb3", a=1.0, step=True, lookup=False):
    """町人（顔は描かない）。(cx, fy)=足もと中央、h=身長（頭の結い髪の先まで）、face=+1 右向き／-1 左向き。
    pose: 'stand' 立つ／'walk' 歩く（t で足が動く）／'wall' 手を前に出して壁（柱）をさぐる"""
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(cx, fy)
    ctx.scale(face, 1)
    u = h / 100.0
    walking = pose in ("walk", "wall")
    ph = t * (7.0 if pose == "walk" else 3.0) if walking else 0.0
    sw = math.sin(ph)
    bob = -abs(math.sin(ph)) * 1.0 * u if walking else (-0.35 * u * math.sin(t * 2.0) if step else 0.0)
    ctx.translate(0, bob)
    lw = 2.6 * u
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    hem = -30 * u
    # 足（着物のすその下）
    for s_, back in ((1, 0), (-1, 1)):
        fx = s_ * sw * 9 * u if walking else s_ * 3.0 * u
        fyy = -max(0.0, s_ * math.cos(ph)) * 4.5 * u if walking else 0.0
        for col, wd in ((INK, lw + 3.4), (SKIN, lw)):
            ctx.set_source_rgba(*hexrgb(col, a))
            ctx.set_line_width(wd)
            ctx.move_to(s_ * 3.0 * u * 0.5, hem)
            ctx.line_to(fx, fyy - 2.0 * u)
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb(INK, a))                                # げた
        ctx.rectangle(fx - 1.5 * u + 0.5 * u, fyy - 2.4 * u, 6.5 * u, 2.4 * u)
        ctx.fill()
    # うしろの腕
    sh_y = -80 * u
    if pose == "wall":
        hands = [((2 * u, sh_y), (14 * u, -66 * u)), ((4 * u, sh_y), (31 * u, -80 * u))]
    elif walking:
        hands = [((0, sh_y), (-sw * 9 * u + 2 * u, -56 * u)), ((0, sh_y), (sw * 9 * u + 2 * u, -56 * u))]
    else:
        hands = [((0, sh_y), (-4 * u, -50 * u)), ((0, sh_y), (6 * u, -52 * u))]
    if umbrella:
        hands[1] = ((4 * u, sh_y), (13 * u, -66 * u))

    def arm(i):
        (sx_, sy_), (hx_, hy_) = hands[i]
        for col, wd in ((INK, lw + 3.4), (kimono, lw + 1.0)):
            ctx.set_source_rgba(*hexrgb(col, a))
            ctx.set_line_width(wd)
            ctx.move_to(sx_, sy_)
            ctx.line_to((sx_ + hx_) / 2 + 1.5 * u, (sy_ + hy_) / 2)
            ctx.line_to(hx_, hy_)
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb(SKIN, a))
        ctx.arc(hx_, hy_, 2.0 * u, 0, 2 * math.pi)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(1.3 * u)
        ctx.arc(hx_, hy_, 2.0 * u, 0, 2 * math.pi)
        ctx.stroke()
    arm(0)
    # 着物
    body = [(-8.6 * u, sh_y), (8.6 * u, sh_y), (11.8 * u, hem), (-11.8 * u, hem)]
    _poly(ctx, body)
    ctx.set_source_rgba(*hexrgb(kimono, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(1.6 * u)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(OBI, a))                                      # 帯
    _poly(ctx, [(-10.0 * u, -56 * u), (10.0 * u, -56 * u), (10.6 * u, -49 * u), (-10.6 * u, -49 * u)])
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#f4ead6", a))                                # えり（V字）
    _poly(ctx, [(-3.8 * u, sh_y), (3.8 * u, sh_y), (0, -69 * u)])
    ctx.fill()
    arm(1)
    # 首・頭・結い髪
    ctx.set_source_rgba(*hexrgb(SKIN, a))
    ctx.rectangle(-1.6 * u, sh_y - 3.5 * u, 3.2 * u, 4.5 * u)
    ctx.fill()
    hx, hy, hr = 0.0, -89.5 * u, 7.0 * u
    if lookup:
        hx += 1.5 * u
    ctx.set_source_rgba(*hexrgb(SKIN, a))
    ctx.arc(hx, hy, hr, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(1.5 * u)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(HAIR, a))                                     # 髪（上半分）と結い髪
    ctx.arc(hx, hy, hr + 0.5 * u, math.pi * 1.12, math.pi * 1.88)
    ctx.fill()
    ctx.save()
    ctx.translate(hx - 5.0 * u, hy - hr - 2.2 * u)
    ctx.rotate(-0.5)
    ctx.scale(1.0, 0.55)
    ctx.arc(0, 0, 3.8 * u, 0, 2 * math.pi)
    ctx.restore()
    ctx.fill()
    # かさ
    if umbrella:
        ux, uy = 13 * u, -66 * u
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(1.3 * u)
        ctx.move_to(ux, uy)
        ctx.line_to(ux, -118 * u)
        ctx.stroke()
        ctx.save()
        ctx.translate(ux, -118 * u)
        ctx.scale(1.0, 0.5)
        ctx.arc(0, 0, 30 * u, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#b8433a", a))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(1.5 * u)
        ctx.stroke()
        for k in range(-2, 3):
            ctx.move_to(ux, -118 * u)
            ctx.line_to(ux + k * 12 * u, -118 * u + (0 if k in (-2, 2) else 0) - (15 * u) * math.sqrt(max(0.0, 1 - (k / 2.5) ** 2)))
        ctx.set_source_rgba(*hexrgb("#f4ead6", a * 0.8))
        ctx.set_line_width(1.0 * u)
        ctx.stroke()
    # 壁（柱）をさぐる手の先
    if pose == "wall":
        ctx.set_source_rgba(*hexrgb("#6b4f33", a))
        ctx.rectangle(33.5 * u, -108 * u, 5.5 * u, 80 * u)
        ctx.fill()
    ctx.restore()


# ---- 提灯 ----
def chochin(ctx, cx, cy, h, lit=1.0, t=0.0, a=1.0):
    """提灯（中に火をともして持ち歩く紙の灯り）。(cx, cy)=本体の中心、h=全体の高さ。lit=0〜1 の火の強さ"""
    if a <= 0.003:
        return
    if lit > 0.01:
        glow(ctx, cx, cy, h * 0.95, "#ffb347", 0.55 * lit * a)
    rx, ry = 0.30 * h, 0.34 * h
    ctx.save()
    ctx.translate(cx, cy)
    # 持ち手
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(3.0, h * 0.02))
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(-0.14 * h, -0.38 * h)
    ctx.curve_to(-0.12 * h, -0.62 * h, 0.12 * h, -0.62 * h, 0.14 * h, -0.38 * h)
    ctx.stroke()
    # 本体
    col0, col1 = hexrgb("#e4dcc4"), hexrgb("#ffd26a")
    cc = [col0[i] + (col1[i] - col0[i]) * lit for i in range(3)]
    ctx.save()
    ctx.scale(1, ry / rx)
    ctx.arc(0, 0, rx, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(cc[0], cc[1], cc[2], a)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(2.5, h * 0.016))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#8a5a2b", 0.8 * a))                          # ひご（横の線）
    ctx.set_line_width(max(2.0, h * 0.012))
    for k in range(-3, 4):
        yy = k * ry * 0.26
        wdt = rx * math.sqrt(max(0.0, 1 - (yy / ry) ** 2))
        ctx.move_to(-wdt, yy)
        ctx.curve_to(-wdt * 0.5, yy + ry * 0.05, wdt * 0.5, yy + ry * 0.05, wdt, yy)
    ctx.stroke()
    # ふた
    ctx.set_source_rgba(*hexrgb("#2b2530", a))
    ctx.rectangle(-0.20 * h, -ry - 0.03 * h, 0.40 * h, 0.07 * h)
    ctx.fill()
    ctx.rectangle(-0.20 * h, ry - 0.04 * h, 0.40 * h, 0.07 * h)
    ctx.fill()
    # 火
    if lit > 0.01:
        fl = 1.0 + 0.10 * math.sin(t * 11) + 0.06 * math.sin(t * 17 + 1)
        ctx.set_source_rgba(*hexrgb("#ff7a1f", a * lit))
        ctx.move_to(0, 0.10 * h)
        ctx.curve_to(0.07 * h, 0.04 * h, 0.03 * h * fl, -0.06 * h * fl, 0, -0.12 * h * fl)
        ctx.curve_to(-0.03 * h * fl, -0.06 * h * fl, -0.07 * h, 0.04 * h, 0, 0.10 * h)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb("#fff2a0", a * lit))
        ctx.arc(0, 0.04 * h, 0.028 * h, 0, 2 * math.pi)
        ctx.fill()
    ctx.restore()


# ---- くじ箱・日記・木戸 ----
def kuji_box(ctx, cx, cy, w, slip=0.0, a=1.0, label=True):
    """くじの箱（上の穴から札が1枚出る）。(cx, cy)=箱の上面の中心。slip=0〜1 で札が出てくる"""
    if a <= 0.003:
        return
    bh = 0.62 * w
    ctx.save()
    ctx.translate(cx, cy)
    # 札（箱のうしろから上へ）
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
    # 前面
    ctx.set_source_rgba(*hexrgb("#b98550", a))
    rrect(ctx, -w / 2, 0, w, bh, 8)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(3.0, w * 0.014))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#8a5c33", 0.6 * a))                        # 木目
    ctx.set_line_width(max(2.0, w * 0.007))
    for k in (0.28, 0.5, 0.74):
        ctx.move_to(-w / 2 + 14, bh * k)
        ctx.line_to(w / 2 - 14, bh * k)
    ctx.stroke()
    # 上面と穴
    ctx.set_source_rgba(*hexrgb("#d7a56c", a))
    _poly(ctx, [(-w / 2, 0), (w / 2, 0), (w / 2 - 0.08 * w, -0.14 * w), (-w / 2 + 0.08 * w, -0.14 * w)])
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


def diary_stack(ctx, cx, cy, w, a=1.0, slip=0.0):
    """日記の束（とじた紙の山）。(cx, cy)=束の中心。slip=0〜1 で1枚が抜ける"""
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(cx, cy)
    for k in range(6):
        ctx.set_source_rgba(*hexrgb("#ece3c6" if k % 2 == 0 else "#f6efd8", a))
        rrect(ctx, -w / 2 + k * 3, -w * 0.18 + k * 7, w, w * 0.62, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.4)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#9a8a6a", 0.7 * a))
    ctx.set_line_width(2.2)
    for k in range(5):
        yy = w * (-0.02 + 0.10 * k)
        ctx.move_to(-w * 0.38, yy + 40)
        ctx.line_to(w * 0.38, yy + 40)
    ctx.stroke()
    if slip > 0:
        ctx.save()
        ctx.translate(w * 0.18 + slip * w * 0.45, -w * 0.18 - slip * w * 0.20)
        ctx.rotate(0.18 * slip)
        rrect(ctx, -w * 0.18, -w * 0.12, w * 0.36, w * 0.28, 5)
        ctx.set_source_rgba(1, 1, 0.97, a)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(2.6)
        ctx.stroke()
        ctx.restore()
    ctx.restore()


def kido_gate(ctx, cx, cy, w, a=1.0):
    """町の入り口の木戸（柱2本・屋根・戸）。(cx, cy)=柱の足もとの中心"""
    if a <= 0.003:
        return
    h = 0.95 * w
    ctx.save()
    ctx.translate(cx, cy)
    for sx in (-1, 1):                                                         # 柱
        ctx.set_source_rgba(*hexrgb("#6b4f33", a))
        ctx.rectangle(sx * w * 0.42 - w * 0.04, -h, w * 0.08, h)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(3)
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#4a3a2a", a))                                  # 屋根
    _poly(ctx, [(-w * 0.58, -h + 4), (w * 0.58, -h + 4), (w * 0.44, -h - w * 0.16), (-w * 0.44, -h - w * 0.16)])
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3)
    ctx.stroke()
    for sx in (-1, 1):                                                         # 戸（左右の板戸）
        ctx.set_source_rgba(*hexrgb("#a98558", a))
        ctx.rectangle(min(0, sx * w * 0.38) + (0 if sx < 0 else 0), -h * 0.82, w * 0.38, h * 0.82)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.set_line_width(2.5)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb("#6b4f33", 0.8 * a))
        for k in range(1, 5):
            ctx.move_to(min(0, sx * w * 0.38) + k * w * 0.076, -h * 0.82)
            ctx.line_to(min(0, sx * w * 0.38) + k * w * 0.076, 0)
        ctx.stroke()
    ctx.restore()


def house(ctx, cx, fy, w, a=1.0, lit=False):
    """小さな家（長屋）。(cx, fy)=足もとの中心"""
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
    _poly(ctx, [(-w * 0.6, -h), (w * 0.6, -h), (w * 0.4, -h - w * 0.3), (-w * 0.4, -h - w * 0.3)])
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#ffd26a" if lit else "#6b4f33", a))
    ctx.rectangle(-w * 0.12, -h * 0.62, w * 0.24, h * 0.62)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.stroke()
    ctx.restore()


def tiny_person(ctx, cx, fy, h, col="#4d6fb3", a=1.0):
    """小さな町人（数をそろえて並べるとき用。2026-10-28 から edo_people の小さい形）"""
    if a > 0.003:
        edo_people.draw_townsman(ctx, cx, fy, h * 1.05, pose="small", kimono=col, a=a)


def tiny_person_old(ctx, cx, fy, h, col="#4d6fb3", a=1.0):
    """小さな町人（数をそろえて並べるとき用。丸い頭＋着物の三角）"""
    ctx.set_source_rgba(*hexrgb(col, a))
    _poly(ctx, [(cx - 0.20 * h, fy - 0.08 * h), (cx + 0.20 * h, fy - 0.08 * h), (cx + 0.10 * h, fy - 0.68 * h), (cx - 0.10 * h, fy - 0.68 * h)])
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(SKIN, a))
    ctx.arc(cx, fy - 0.82 * h, 0.15 * h, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(max(1.2, h * 0.05))
    ctx.arc(cx, fy - 0.82 * h, 0.15 * h, 0, 2 * math.pi)
    ctx.stroke()
    ctx.move_to(cx - 0.08 * h, fy - 0.08 * h)
    ctx.line_to(cx - 0.08 * h, fy)
    ctx.move_to(cx + 0.08 * h, fy - 0.08 * h)
    ctx.line_to(cx + 0.08 * h, fy)
    ctx.stroke()


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


# ============================================================
# 1人に寄る場面（舞台）: 空の窓（月の満ち欠けと高さ）・通り・町人・右下の「明るさ」の目盛りと「歩ける線」・1時間の帯
# ============================================================
SKY_Y0, SKY_Y1 = 180, 420                    # 空の窓
STREET_Y0, STREET_Y1 = 420, 930              # 通り
FEET = 895                                   # 町人の足もと
PERSON_H = 470                               # 町人の身長（画面の高さ 1080 の 44%）
G_MAX = 0.20                                 # 目盛りの上端（lx）。歩ける線 0.05 は下から 25%


class Walk:
    """1人ぶんの60分（1分刻みの照度 E・月の高さ・空が見えるか・月の光っている割合）"""

    def __init__(self, E, alt, vis, lday, lit, waxing, rain=False, name="", sky_txt=""):
        self.E, self.alt, self.vis, self.lday, self.lit, self.waxing = list(E), list(alt), bool(vis), lday, lit, waxing
        self.rain, self.name, self.sky_txt = rain, name, sky_txt

    @classmethod
    def card(cls, c, name=""):
        return cls(c["series"]["E"], c["series"]["moon_alt"], c["sky_visible"], c["lday"], c["moon_lit_percent"] / 100.0,
                   c["lday"] <= 15, rain=c["sky"] in ("雨雪", "曇"), name=name, sky_txt=c["sky"])

    def m_of(self, u):
        return int(min(WALK - 1, max(0, round(clamp01(u) * (WALK - 1)))))

    def eff(self, m):
        return self.E[m] if self.vis else 0.0

    def walkable(self, m):
        return sum(1 for k in range(m + 1) if self.eff(k) >= LINE)

    @property
    def total(self):
        return self.walkable(WALK - 1)


def _synthetic_sample():
    """見本の1時間（歩ける線の下から始まり、20分ごろに線をまたぐ）。照度の並びは なめらかな見本で、実データではない"""
    E = [0.02 + 0.095 * ease_in_out(m / 59.0) for m in range(WALK)]
    alt = [24 + 22 * (m / 59.0) for m in range(WALK)]
    return Walk(E, alt, True, 12, 0.93, True, name="見本")


W9 = Walk.card(SD["people"]["n9"], "九夜")
W15 = Walk.card(SD["people"]["n15"], "十五夜")
W16 = Walk.card(SD["people"]["n16"], "十六夜")
WWIN = Walk.card(SD["people"]["winter14"], "冬")
WTSU = Walk.card(SD["people"]["tsuyu"], "梅雨")
WSUM = Walk.card(SD["people"]["summer"], "夏")        # 夏の晴れた、満月のころの人（1万人から。雲はないが月が低く、目盛りは線の下）
WCLOUD = Walk([0.075] * WALK, [32.0] * WALK, True, 15, 1.0, True, name="雲の例")   # 雲の説明に使う別の町人（満月の晴れた夜。実データではなく例）
WWORST = Walk.card(WORST, "最悪")
WBEST = Walk.card(BEST, "最良")
WSAMPLE = _synthetic_sample()


def street(ctx, x0, x1, dark, t, scroll=0.0, a=1.0):
    """通り（うしろの板壁と地面）。dark=0〜1 で夜の暗さ（藍）をかぶせる"""
    y0, y1 = STREET_Y0, STREET_Y1
    ctx.save()
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
    ctx.clip()
    ctx.set_source_rgba(*hexrgb("#d9c6a0", a))
    ctx.rectangle(x0, y0, x1 - x0, 360)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#b9a67e", 0.7 * a))
    ctx.set_line_width(3)
    sp = 74
    k0 = int((x0 - scroll) // sp) - 1
    for k in range(k0, k0 + int((x1 - x0) / sp) + 3):
        xx = k * sp + scroll
        ctx.move_to(xx, y0 + 18)
        ctx.line_to(xx, y0 + 360)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#6b5a40", a))
    ctx.rectangle(x0, y0, x1 - x0, 20)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#bfae86", a))
    ctx.rectangle(x0, y0 + 360, x1 - x0, y1 - y0 - 360)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#8f7e5c", 0.6 * a))
    ctx.set_line_width(3)
    for k, yy in enumerate((y0 + 395, y0 + 440, y0 + 480)):
        ctx.move_to(x0, yy)
        ctx.line_to(x1, yy)
    ctx.stroke()
    if dark > 0.003:
        ctx.set_source_rgba(*hexrgb("#0a1233", dark * a))
        ctx.rectangle(x0, y0, x1 - x0, y1 - y0)
        ctx.fill()
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(3.5)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 18)
    ctx.stroke()


def ruler(ctx, x0, horizon, top, alt, label=True, a=1.0, col="#e9edff"):
    """窓の左の「月の高さ」の目盛り。alt（度）の位置に三角。地平線の下なら下の端に赤い三角と「地平線の下」"""
    xr = x0 + 40
    ctx.set_source_rgba(*hexrgb(col, 0.9 * a))
    ctx.set_line_width(4)
    ctx.move_to(xr, horizon)
    ctx.line_to(xr, top)
    ctx.stroke()
    for deg in (0, 45, 90):
        yy = horizon - deg / 90 * (horizon - top)
        ctx.move_to(xr - 9, yy)
        ctx.line_to(xr + 9, yy)
    ctx.stroke()
    below = alt <= 0
    yy = horizon - clamp01(alt / 90) * (horizon - top)
    ctx.set_source_rgba(*hexrgb("#ff7a7a" if below else GOLD, a))
    _poly(ctx, [(xr + 8, yy), (xr + 30, yy - 11), (xr + 30, yy + 11)])
    ctx.fill()
    if label:
        text(ctx, "月の高さ", x0 + 18, SKY_Y0 + 32, 52, col, align="left", alpha=a)
    if below:
        text(ctx, "地平線の下", xr + 40, horizon - 40, 52, "#ffb0b0", align="left", alpha=a)


def gauge(ctx, box, level, a=1.0, hi_bar=0.0, hi_line=0.0, t=0.0, title="明るさ", size=56, lsize=52):
    """右下の「明るさ」の縦の目盛りと、横の「歩ける線」。level=いまの月明かり（lx）。箱 (x0,y0,x1,y1)"""
    if a <= 0.003:
        return
    x0, y0, x1, y1 = box
    ctx.set_source_rgba(1, 1, 1, 0.78 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    text(ctx, title, x0 + 24, y0 + 42, size, INK, align="left", alpha=a)
    bx0, bx1 = x0 + 34, x0 + 90
    yt, yb = y0 + 100, y1 - 28
    ctx.set_source_rgba(*hexrgb("#e8e4d6", a))
    rrect(ctx, bx0, yt, bx1 - bx0, yb - yt, 8)
    ctx.fill()

    def yv(e):
        return yb - clamp01(e / G_MAX) * (yb - yt)
    lv = clamp01(level / G_MAX)
    if lv > 0.002:
        ctx.set_source_rgba(*hexrgb(GOLD, 0.95 * a))
        rrect(ctx, bx0, yv(level), bx1 - bx0, yb - yv(level), 8)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(3)
    rrect(ctx, bx0, yt, bx1 - bx0, yb - yt, 8)
    ctx.stroke()
    if hi_bar > 0.003:
        pen_circle(ctx, (bx0 + bx1) / 2, (yt + yb) / 2, 52, (yb - yt) / 2 + 20, RED, seed=5, width=6, progress=hi_bar, alpha=a)
    # 歩ける線
    ly = yv(LINE)
    above = level >= LINE
    ctx.set_source_rgba(*hexrgb(BLUE if above else RED, a))
    ctx.set_line_width(5)
    ctx.set_dash([14, 9])
    ctx.move_to(bx0 - 10, ly)
    ctx.line_to(x1 - 18, ly)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "歩ける線", bx1 + 36, ly - 36, lsize, BLUE if above else RED, align="left", alpha=a)
    if hi_line > 0.003:
        pen_circle(ctx, (bx1 + x1) / 2 - 4, ly - 14, (x1 - bx1) / 2 + 6, 46, RED, seed=8, width=6, progress=hi_line, alpha=a)
    # いまの高さ（三角）
    cy = yv(level)
    ctx.set_source_rgba(*hexrgb(INK, a))
    _poly(ctx, [(bx1 + 4, cy), (bx1 + 30, cy - 13), (bx1 + 30, cy + 13)])
    ctx.fill()


def strip(ctx, x0, y0, w, wk, m_now, a=1.0, title="帰り道の1時間", total=True, size=52):
    """帰り道の1時間（60マス）の帯。歩けた分（線の上にいた分）を青く塗る。m_now まで塗り、そのあとは空"""
    if a <= 0.003:
        return
    text(ctx, title, x0, y0, size, INK, align="left", alpha=a)
    cw = w / WALK
    yy = y0 + 28
    ctx.set_source_rgba(1, 1, 1, 0.75 * a)
    rrect(ctx, x0 - 4, yy - 4, w + 8, 52, 8)
    ctx.fill()
    for m in range(WALK):
        if m <= m_now:
            col = BLUE if wk.eff(m) >= LINE else DIM
            ctx.set_source_rgba(*hexrgb(col, a))
        else:
            ctx.set_source_rgba(*hexrgb("#e9e3d3", a))
        ctx.rectangle(x0 + m * cw + 0.6, yy, cw - 1.2, 44)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
    ctx.set_line_width(2.5)
    rrect(ctx, x0 - 4, yy - 4, w + 8, 52, 8)
    ctx.stroke()
    if total:
        n = wk.walkable(m_now)
        text(ctx, f"歩けた分 {n}分", x0, yy + 108, 64, BLUE if n > 0 else INK, align="left", alpha=a)


def stage_core(ctx, t, x0, x1, wk, u, pose="walk", umbrella=False, clouds=None, rain=None, ruler_on=True, ruler_label=True, kind=None, px=None,
               shadow=0.0, scroll_on=None, a=1.0, hide_moon=False, path_home=0.0, person_a=1.0, face=1, moon_x=0.60, dark=None, lookup=False, kimono="#4d6fb3"):
    """空の窓＋通り＋町人。wk=Walk、u=帰り道の進み 0〜1。戻り値 (m, E_eff)"""
    m = wk.m_of(u)
    e_eff = wk.eff(m)
    alt = wk.alt[m]
    if clouds is None:
        clouds = 0.0 if wk.vis else 0.92
    if rain is None:
        rain = wk.rain and not wk.vis and wk.sky_txt == "雨雪"
    if kind is None:
        kind = "night"
    horizon = sky_window(ctx, x0, SKY_Y0, x1, SKY_Y1, t, kind=kind, clouds=clouds, rain=rain, a=a)
    top = SKY_Y0 + 62
    if alt > 0 and not hide_moon:
        my = horizon - clamp01(alt / 90) * (horizon - top) - 6
        ctx.save()
        rrect(ctx, x0, SKY_Y0, x1 - x0, SKY_Y1 - SKY_Y0, 18)
        ctx.clip()
        moon_disc(ctx, x0 + moon_x * (x1 - x0), my, 38, wk.lit, wk.waxing, a=a * ((1.0 - 0.85 * clouds) if wk.vis else 0.28), halo=(0.9 * (1 - clouds)) if wk.vis else 0.0)
        ctx.restore()
        if (not wk.vis) or clouds > 0.35:
            ctx.save()
            rrect(ctx, x0, SKY_Y0, x1 - x0, SKY_Y1 - SKY_Y0, 18)
            ctx.clip()
            cloud(ctx, x0 + moon_x * (x1 - x0), my + 6, 300, "#7b839c", 0.9 * a * (1.0 if not wk.vis else clamp01((clouds - 0.35) / 0.4)))
            ctx.restore()
    if ruler_on:
        ruler(ctx, x0, horizon, top, alt, label=ruler_label, a=a)
    if dark is None:
        dark = 0.08 + 0.48 * (1 - clamp01(e_eff / 0.12))
    if scroll_on is None:
        scroll_on = pose == "walk"
    street(ctx, x0, x1, dark, t, scroll=-(t * 190.0) if scroll_on else (-(t * 60.0) if pose == "wall" else 0.0), a=a)
    pxx = px if px is not None else x0 + 0.47 * (x1 - x0)
    if shadow > 0:
        ctx.set_source_rgba(0.06, 0.08, 0.2, 0.30 * a)
        ctx.save()
        ctx.translate(pxx - shadow * 0.5 * face, FEET + 8)
        ctx.scale(shadow * 0.5, 15)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if path_home > 0.003:
        hx = (x1 - 120) if (x1 - x0) > 900 else min(x1 - 120, pxx + 150)
        ctx.set_source_rgba(*hexrgb(INK, 0.55 * a * path_home))
        ctx.set_line_width(5)
        ctx.set_dash([4, 14])
        ctx.move_to(pxx + 70, FEET + 18)
        ctx.line_to(hx - 60, FEET + 18)
        ctx.stroke()
        ctx.set_dash([])
        house(ctx, hx, FEET + 14, 110 if hx < x1 - 130 else 130, a=a * path_home)
    person(ctx, pxx, FEET, PERSON_H, t=t, pose=pose, face=face, umbrella=umbrella, a=a * person_a, lookup=lookup, kimono=kimono, night=True)
    return m, e_eff


def stage_single(ctx, t, wk, u, show_gauge=True, show_strip=True, strip_total=True, hi_bar=0.0, hi_line=0.0, a=1.0, strip_title="帰り道の1時間", ga=1.0, sa=1.0,
                 level_mult=1.0, **kw):
    """1人に寄る場面（左の2/3に空の窓と通りと町人、右の列に1時間の帯、右下に目盛り）"""
    m, e = stage_core(ctx, t, 60, 1040, wk, u, a=a, **kw)
    if show_strip:
        strip(ctx, 1090, 70, 760, wk, m, a=a * sa, total=strip_total, title=strip_title)
    if show_gauge:
        gauge(ctx, (1470, 450, 1850, 925), e * level_mult, a=a * ga, hi_bar=hi_bar, hi_line=hi_line, t=t)
    return m, e


HALF = {"L": (60, 930), "R": (990, 1860)}


def stage_half(ctx, t, side, wk, u, show_gauge=True, hi_bar=0.0, hi_line=0.0, a=1.0, level_mult=1.0, **kw):
    """左右に並べる場面の片側（空の窓・通り・町人・その人の目盛り）"""
    x0, x1 = HALF[side]
    kw.setdefault("px", x0 + 0.33 * (x1 - x0))
    kw.setdefault("moon_x", 0.62)
    m, e = stage_core(ctx, t, x0, x1, wk, u, a=a, **kw)
    if show_gauge:
        gauge(ctx, (x1 - 340, 450, x1 - 10, 922), e * level_mult, a=a, hi_bar=hi_bar, hi_line=hi_line, t=t, lsize=46)
    return m, e


# ============================================================
# 1万マス（100×100）: 帰れた人だけ明るく
# ============================================================
class PeopleGrid:
    """100×100 のマスに1万人。cls=マスごとの区分（0,1,2…。行の左から右・上から下の順）。pal_dim/pal_lit=区分ごとの色（まだ光らないとき／光ったとき）。
    n_fill 個までのマスが現れ、lit 区分のマスは n_lit 個（ランダムな順）だけ光る。マスは 4.4px・1マス＝1人"""

    def __init__(self, cls, pal_dim, pal_lit, lit_cls=1, cx=492, y0=170.0, cell=4.4, side=100, seed=3):
        self.n = side * side
        self.side, self.cell, self.cx, self.y0 = side, cell, cx, y0
        self.px = int(round(side * cell))
        self.x0 = cx - self.px / 2
        self.cls = np.asarray(cls)
        assert len(self.cls) == self.n
        px = self.px
        self.idx = np.full((px, px), 10 ** 9, np.int64)
        for i in range(self.n):
            r_, q_ = i // side, i % side
            ya, yb = int(round(r_ * cell)), int(round((r_ + 1) * cell)) - 1
            xa, xb = int(round(q_ * cell)), int(round((q_ + 1) * cell)) - 1
            self.idx[ya:yb, xa:xb] = i
        valid = self.idx < 10 ** 9
        safe = np.where(valid, self.idx, 0)
        self.pix_cls = np.where(valid, self.cls[safe], -1)

        def bgra(h):
            r, g, b = hexrgb(h)[:3]
            return np.array([int(b * 255), int(g * 255), int(r * 255), 255], np.uint8)
        self.img_dim = np.zeros((px, px, 4), np.uint8)
        self.img_lit = np.zeros((px, px, 4), np.uint8)
        for c_, h in pal_dim.items():
            self.img_dim[self.pix_cls == c_] = bgra(h)
        for c_, h in pal_lit.items():
            self.img_lit[self.pix_cls == c_] = bgra(h)
        self.img_empty = np.zeros((px, px, 4), np.uint8)
        self.img_empty[valid] = bgra("#e9e3d3")
        order = np.full(self.n, 10 ** 9, np.int64)
        wins = np.nonzero(self.cls == lit_cls)[0]
        order[wins] = np.random.default_rng(seed).permutation(len(wins))
        self.rank_pix = np.where(valid, order[safe], 10 ** 9)
        self.n_lit_total = len(wins)
        self.lit_cls = lit_cls
        self.flag = None

    def draw(self, ctx, n_fill, n_lit=0, a=1.0):
        if a <= 0.003:
            return
        n_fill = int(max(0, min(self.n, n_fill)))
        img = np.where((self.idx < n_fill)[..., None], self.img_dim, self.img_empty)
        if n_lit > 0:
            img = np.where(((self.rank_pix < n_lit) & (self.idx < n_fill))[..., None], self.img_lit, img)
        buf = np.ascontiguousarray(img)
        s = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, self.px, self.px, self.px * 4)
        ctx.set_source_surface(s, self.x0, self.y0)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(self.x0 - 4, self.y0 - 4, self.px + 6, self.px + 6)
        ctx.stroke()

    def row_y(self, frac):
        """上から frac（0〜1）の高さの y"""
        return self.y0 + frac * self.px

    def check(self, n_expect_lit):
        probs = []
        if int((self.cls == self.lit_cls).sum()) != n_expect_lit:
            probs.append(f"光るマス {int((self.cls == self.lit_cls).sum())} ≠ {n_expect_lit}")
        if self.side * self.side != self.n:
            probs.append(f"{self.side}×{self.side} ≠ {self.n}")
        return probs


# ============================================================
# 場面の仕組み: 場面 = (名前, 始め, 終わり, 描く関数)。前の場面が消えきってから（0.2秒）次が出る＝文字が重ならない
#   場面の始めは、その場面の最初の文の頭の 1.05秒前（絵は声より先に。枠は声の0.5秒前までにそろう）。
#   ただし前の文の終わりより前にはしない（bd）。第1章からは切りかえの前の間を SCENE_GAP 秒にしてある（_pace）
# ============================================================
SCENES = []
SC_IN, SC_OUT, SC_DELAY = 0.25, 0.2, 0.2


def scene(name, t0, t1, fn, first=False):
    SCENES.append((name, t0, t1, fn, first))


SC_FAST = {"grid": (0.0, 0.2)}          # 場面ごとの出かた（遅れ・フェード）。1万マスは前の文の終わりから すぐ出す（0章は間を足せない）


def draw_scenes(ctx, t):
    for name, t0, t1, fn, first in SCENES:
        if t < t0 - 1e-6 or t > t1 + SC_OUT:
            continue
        dl, fi = SC_FAST.get(name, (SC_DELAY, SC_IN))
        a_in = 1.0 if first else ease_out(clamp01((t - t0 - dl) / fi))
        a = a_in * (1.0 - clamp01((t - t1) / SC_OUT))
        grp(ctx, a, fn, t)


def bd(key, lead=1.05):
    """場面の始め（その文の頭の lead 秒前。ただし前の文の終わりより前にはしない＝前の場面を文の途中で消さない）"""
    t = Sk(key) - lead
    p = PREV_LINE.get(ID[key])
    return max(t, E(p)) if p else t


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


# ============================================================
# 0 冒頭（0秒目から。左に月夜・右に闇夜。声は0.5秒から）
# ============================================================
QLINES = ["提灯なしで、家に帰れる？"]
QTXT = "".join(QLINES)                                  # 題名・サムネと同じ言葉
WOPEN_L = Walk([0.10] * WALK, [38.0] * WALK, True, 15, 1.0, True, name="月夜")
WOPEN_R = Walk([0.0] * WALK, [-30.0] * WALK, True, 29, 0.0, False, name="闇夜")
T_LAN0 = Sk("c0_lan") - 0.5                             # 提灯が出る
T_LAN_OFF = Sk("c0_forgot", 0.0) + 0.2                  # 火が消える


def sc_open(ctx, t):
    text(ctx, QTXT, 960, 100, 100, INK)
    pen_line(ctx, 372, 156, 1572, 150, RED, seed=5, width=8, progress=clamp01(t / 0.7), alpha=0.9)
    stage_core(ctx, t + 1.7, 60, 930, WOPEN_L, 0.5, pose="walk", ruler_on=False, shadow=210, dark=0.04, clouds=0.0)
    stage_core(ctx, t + 0.4, 990, 1860, WOPEN_R, 0.5, pose="wall", ruler_on=False, kind="dark", dark=0.66, clouds=0.30, hide_moon=True)
    mini_sticky(ctx, "月夜", 200, 250, 56, "yellow", align="center", tilt=-0.02)
    mini_sticky(ctx, "闇夜", 1130, 250, 56, "pink", align="center", tilt=0.02)
    lit = fade(t, T_LAN0, 0.4) * (1.0 - clamp01((t - T_LAN_OFF) / 0.7))
    chochin(ctx, 960, 640, 270, lit=lit, t=t, a=fade(t, T_LAN0, 0.4))


T_W9G = Sk("c0_drew") + 0.4                           # 目盛り（明るさと歩ける線）が出る


def sc_walk9(ctx, t):
    t_left = Sk("c0_left") + 0.4
    t_end = Ek("c0_dark") - 0.3
    u = clamp01((t - t_left) / (t_end - t_left))
    t_dk = Sk("c0_dark", 0.35)
    dark = lerp(0.32, 0.80, ease_in_out(clamp01((t - t_dk) / 3.0)))
    stage_single(ctx, t, W9, u, pose="walk" if t >= t_left else "stand", dark=dark, ga=fade(t, T_W9G, 0.4),
                 sa=fade(t, Sk("c0_left") + 0.3, 0.4), strip_total=True)
    stk(ctx, t, "c0_drew", "旧暦9日・晴れ\n月は半分ほど", 60, 107, "yellow", size=48, off=0.2, tilt=-0.008)
    stk(ctx, t, "c0_left", "暮六つ\n日が暮れて\n手もとが暗くなるころ", 1090, 350, "mint", size=44, off=0.3, tilt=0.008)


# ---- 1万マス（100×100）----
_RNG0 = np.random.default_rng(20261027)
_CLS0 = np.zeros(N, int)
_CLS0[:N_ALL] = 1
_CLS0 = _RNG0.permutation(_CLS0)
GRID_OPEN = PeopleGrid(_CLS0, {0: "#cdd0dc", 1: "#cdd0dc"}, {0: "#cdd0dc", 1: "#1f5fd0"}, lit_cls=1, cx=LCX, y0=180.0, cell=5.0, seed=11)
T_GRID0 = bd("c0_10k")                                   # 1万マスの枠（読み方と箱）が出る。前の文（c0_dark）を言い終えてから（0章は間を足せないので、声の頭の0.3秒前）
T_GRID_FILL = (Sk("c0_10k", 0.1), Ek("c0_10k") - 0.5)
T_LIGHT0 = Sk("c0_res", 0.45)                            # 帰れた人だけ明るくなる
T_LIGHT1 = T_LIGHT0 + 2.0                                # 光るのは2秒かけて（積み上がるアニメは全体で2秒以上）
COND_ROWS = [("場所: 日本橋あたり", "c0_cond", 0.0), ("道: 1里・約1時間", "c0_cond", 0.7), ("時刻: 暮六つ〜夜四つ", "c0_cond", 1.4),
             ("夜と天気: 江戸の日記からくじ", "c0_cond", 2.1), ("歩ける明るさ:\n満月の夜の暗めの明るさ（仮定）", "c0_cond", 2.8)]


def cond_sticky(ctx, t):
    t0 = Sk("c0_cond") - 0.2
    a = fade(t, t0, 0.4)
    if a <= 0.003:
        return
    x0, y0, w, h = RX - 12, 262, 790, 570
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
    text(ctx, "条件", RX + 20, y0 + 44, 44, RED, align="left", alpha=a)
    yc = y0 + 100
    centers = []
    for s_, key, off in COND_ROWS:
        n_ = s_.count("\n") + 1
        cy = yc + n_ * 58 / 2
        centers.append((cy, n_))
        wr(ctx, s_, RX + 20, cy, 48, INK, Sk(key) + off, t, align="left", alpha=a)
        yc += n_ * 58 + 22
    ctx.restore()
    # 「仮定」を赤ペンで囲む
    pa = clamp01((t - Sk("c0_assume", 0.15)) / 0.8)
    if pa > 0:
        cy, n_ = centers[-1]
        pen_circle(ctx, RX + 330, cy, 365, 24 + n_ * 26, RED, seed=7, width=6, progress=pa, alpha=a)


def sc_grid(ctx, t):
    cap_a = fade(t, T_GRID0, 0.25)
    text(ctx, "青＝帰れた　1マス＝1人", LCX, GRID_OPEN.y0 - 44, 56, INK, alpha=cap_a)
    f0, f1 = T_GRID_FILL
    nf = int(N * clamp01((t - f0) / (f1 - f0)) ** 1.7) if t >= T_GRID0 + 0.3 else 0
    nl = int(GRID_OPEN.n_lit_total * ease_in_out(clamp01((t - T_LIGHT0) / (T_LIGHT1 - T_LIGHT0))))
    GRID_OPEN.draw(ctx, nf, nl, a=fade(t, T_GRID0, 0.25))
    qa = fade(t, T_LIGHT1 - 0.2, 0.4)
    text(ctx, f"1万人のうち {N_ALL:,}人", LCX, GRID_OPEN.y0 + GRID_OPEN.px + 100, 66, BLUE, alpha=qa)
    # 結果の数字（声に合わせて）
    ra = fade(t, Sk("c0_res", 0.5), 0.4)
    if ra > 0.003:
        mini_sticky(ctx, f"100人に{P_ALL}人", RCX, 170, 104, "pink", fg=RED, a=ra, tilt=-0.012)
    # くじの箱（右ページ。1万人の文のあいだだけ。条件の札が出る前に消える）
    ka = fade(t, T_GRID0 + 0.2, 0.3) * out_fade(t, Sk("c0_cond") - 0.6, 0.3)
    if ka > 0.003:
        kuji_box(ctx, RCX, 540, 380, slip=ease_in_out(clamp01((t - (Sk("c0_10k") + 0.3)) / 1.0)), a=ka)
        mini_sticky(ctx, "夜と天気を、くじで選ぶ", RCX, 850, 54, "yellow", a=ka, tilt=-0.012)
    cond_sticky(ctx, t)


# ---- 3つの問いの札 ----
TAGS = [("問い1\nいちばん悪い夜と\nいちばん良い夜は？", 330, "c0_q1", "yellow"), ("問い2\n満月のころなら、\nだれでも帰れる？", 960, "c0_q2", "mint"),
        ("問い3\n冬と夏、\n帰れる夜が多いのは？", 1590, "c0_q3", "pink")]


def sc_tags(ctx, t):
    t_all = Sk("c0_next") + 0.2
    for k, (s_, x_, key, col) in enumerate(TAGS):
        a = fade(t, t_all + 0.25 * k, 0.4)
        on = fade(t, Sk(key, 0.0), 0.3) * out_fade(t, Ek(key) + 0.2, 0.3) if key else 0
        mini_sticky(ctx, s_, x_, 470, 46, col, a=a * (0.55 + 0.45 * on), tilt=-0.015 + 0.015 * k)
        if on > 0.003:
            pen_circle(ctx, x_, 470, 255 if k != 2 else 275, 135, RED, seed=3 + k, width=6, progress=clamp01((t - Sk(key)) / 0.7), alpha=on * a)


# ============================================================
# 第1章 いちばん悪い夜と、いちばん良い夜は？
# ============================================================
def seq(t, s, e, fi=0.25, fo=0.15):
    """s〜e の間だけ 1（前の絵が消えきってから次が出る）"""
    return fade(t, s, fi) * (1.0 - clamp01((t - (e - fo)) / fo))


def moon_row_item(ctx, cx, cy, r, L, a=1.0, dim=1.0):
    """旧暦 L 日の夕方の月（紙の上に置く用。暗い所は藍）"""
    moon_disc(ctx, cx, cy, r, lit_of_lday(L), waxing=L <= 15, a=a * dim, dark_col="#2b3358", dark_a=0.92, edge=INK)


def sc_c1_title(ctx, t):
    t_ti = S("ch1") + T_TITLE + 0.3
    title_hand(ctx, "問い1", RX, 150, 110, 6, fade(t, t_ti, 0.4))
    stk(ctx, t, "c1_intro", "いちばん悪かった夜と、\nいちばん良かった夜は、\nどんな夜？", RX, 340, "yellow", size=52, off=1.4, tilt=-0.012)
    t_y = Sk("c1_yoso") + 0.2
    stk(ctx, t, "c1_yoso", "予想", RX, 600, "pink", fg=RED, size=64, off=0.2, until=Sk("c1_yoso2", 0.0) - 0.3, tilt=0.01)
    stk(ctx, t, "c1_yoso2", "予想\n悪い夜＝月のない夜\n月が出ていれば帰れる", RX, 640, "pink", size=48, off=0.5, tilt=0.01)


def sc_c1_moon(ctx, t):
    a = fade(t, bd("c1_moon") + 0.2, 0.4)
    sky_window(ctx, 60, 190, 930, 480, t, kind="night", a=a)
    # 月の光（月から道へ）
    mx, my = 330, 335
    ctx.save()
    g = cairo.LinearGradient(0, my, 0, 860)
    g.add_color_stop_rgba(0, *hexrgb(GOLD, 0.40 * a))
    g.add_color_stop_rgba(1, *hexrgb(GOLD, 0.0))
    ctx.set_source(g)
    _poly(ctx, [(mx - 40, my + 30), (mx + 40, my + 30), (700, 860), (140, 860)])
    ctx.fill()
    ctx.restore()
    moon_disc(ctx, mx, my, 70, 0.9, waxing=True, a=a, halo=0.9)
    ctx.set_source_rgba(*hexrgb("#bfae86", 0.8 * a))                  # 道
    ctx.rectangle(60, 640, 870, 240)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(3.5)
    ctx.rectangle(60, 640, 870, 240)
    ctx.stroke()
    glow(ctx, 400, 760, 300, GOLD, 0.35 * a)
    house(ctx, 760, 700, 130, a=a)
    stk(ctx, t, "c1_moon", "月明かり＝\n月の光で、道がぼんやり\n見える、その明るさ", RX, 420, "yellow", size=52, off=0.2, tilt=-0.01)


def sc_c1_rules(ctx, t):
    # くじの箱 → 日記 → 天気 → 木戸（左ページ）。出かける時刻の帯は全幅
    s_k, s_d, s_w, s_t, s_g = Sk("c1_kuji") - 0.4, Sk("c1_diary") - 0.4, Sk("c1_weather") - 0.4, Sk("c1_time") - 0.4, 1e9
    a_box = seq(t, s_k, s_d)
    if a_box > 0.003:
        kuji_box(ctx, LCX, 400, 420, slip=ease_in_out(clamp01((t - (s_k + 0.9)) / 1.0)), a=a_box)
    a_dia = seq(t, s_d, s_w)
    if a_dia > 0.003:
        diary_stack(ctx, LCX, 470, 470, a=a_dia, slip=ease_in_out(clamp01((t - (s_d + 0.9)) / 1.1)))
        mini_sticky(ctx, "江戸の日記", LCX, 250, 54, "yellow", a=a_dia, tilt=-0.012)
    a_wea = seq(t, s_w, s_t)
    if a_wea > 0.003:
        for k, (nm, cx_) in enumerate((("晴れ", 290), ("雨", 700))):
            ctx.set_source_rgba(1, 1, 1, 0.8 * a_wea)
            rrect(ctx, cx_ - 170, 280, 340, 330, 18)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * a_wea))
            ctx.set_line_width(3)
            rrect(ctx, cx_ - 170, 280, 340, 330, 18)
            ctx.stroke()
            if k == 0:
                sun_disc(ctx, cx_, 410, 56, a=a_wea)
            else:
                cloud(ctx, cx_, 380, 250, "#8e96ad", a_wea)
                ctx.set_source_rgba(*hexrgb("#4f7fcf", a_wea))
                ctx.set_line_width(5)
                ctx.set_line_cap(cairo.LINE_CAP_ROUND)
                for dx in (-70, -20, 30, 80):
                    ctx.move_to(cx_ + dx, 440)
                    ctx.line_to(cx_ + dx - 10, 480)
                ctx.stroke()
            text(ctx, nm, cx_, 550, 64, INK, alpha=a_wea)
    # 出かける時刻の帯（全幅）
    a_b = fade(t, s_t - 0.5, 0.4)
    if a_b > 0.003:
        bx0, bx1, by = 170, 1750, 645
        ctx.set_source_rgba(1, 1, 1, 0.85 * a_b)
        rrect(ctx, bx0, by - 36, bx1 - bx0, 72, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a_b))
        ctx.set_line_width(3)
        rrect(ctx, bx0, by - 36, bx1 - bx0, 72, 12)
        ctx.stroke()
        text(ctx, "暮六つ", bx0, by + 76, 46, INK, align="left", alpha=a_b)
        text(ctx, "夜四つ", bx1, by + 76, 46, INK, align="right", alpha=a_b)
        xa = lerp(bx0 + 120, bx1 - 400, fade(t, Sk("c1_time", 0.55), 0.5))
        ar = fade(t, Sk("c1_time", 0.45), 0.5)
        if ar > 0.003:
            arrow2(ctx, (xa, by - 130 + 60 * ar), (xa, by - 44), RED, w=7, a=ar, head=24)
        mini_sticky(ctx, "出かける時刻は、くじで決める", 960, 470, 48, "yellow", a=a_b, tilt=-0.01)


PH_L = [1, 4, 8, 12, 15, 19, 22, 26, 29]
PH_X = [150 + i * (1620 / 8) for i in range(9)]


def sc_c1_phases(ctx, t):
    for i, (L, x_) in enumerate(zip(PH_L, PH_X)):
        a = fade(t, Sk("c1_cal") - 0.3 + 0.25 * i, 0.3)
        moon_row_item(ctx, x_, 520, 64, L, a=a)
        text(ctx, f"{L}日", x_, 628, 48, INK, alpha=a)
    stk(ctx, t, "c1_kyu", "旧暦", 960, 250, "yellow", size=64, off=0.1, tilt=-0.015, align="center")
    # 1日（月のない夜）・15日（満月）・29日（また月のない夜）に赤ペンの丸
    for key, i, sd in (("c1_new", 0, 3), ("c1_full", 4, 4), ("c1_wane", 8, 5)):
        pa = clamp01((t - Sk(key, 0.1)) / 0.7)
        if pa > 0:
            pen_circle(ctx, PH_X[i], 520, 92, 92, RED, seed=sd, width=6, progress=pa)
    # 1日→15日→29日の矢印
    p1 = clamp01((t - Sk("c1_full", 0.0)) / 1.0)
    if p1 > 0:
        pen_line(ctx, PH_X[0] + 90, 400, PH_X[4] - 90, 400, RED, seed=21, width=6, progress=p1)
        if p1 >= 1:
            arrowhead(ctx, (PH_X[4] - 90, 400), (1, 0), RED, 26, 1.0, 6)
    p2 = clamp01((t - Sk("c1_wane", 0.0)) / 1.2)
    if p2 > 0:
        pen_line(ctx, PH_X[4] + 90, 400, PH_X[8] - 90, 400, RED, seed=23, width=6, progress=p2)
        if p2 >= 1:
            arrowhead(ctx, (PH_X[8] - 90, 400), (1, 0), RED, 26, 1.0, 6)
    # 台詞に合わせて、月の形を1つずつ大きく描き足す（2026-10-31 同じ絵は15秒まで）
    #   「1日が、月のない夜」→ 新月 ／「15日ごろに、満月」→ 満月 ／「月の終わりには、ふたたび月のない夜」→ 細い月 → 新月
    for x_, t0_, lab, kind in BIG_MOONS:
        pop = ease_out(clamp01((t - t0_) / 0.45))
        if pop <= 0.003:
            continue
        r_ = 78 * (0.6 + 0.4 * pop)
        if kind == "new":
            moon_disc(ctx, x_, BIG_MOON_Y, r_, 0.0, waxing=True, a=pop, dark_col="#2b3358", dark_a=0.92, edge=INK)
        elif kind == "full":
            glow(ctx, x_, BIG_MOON_Y, 150, GOLD, 0.45 * pop)
            moon_disc(ctx, x_, BIG_MOON_Y, r_, 1.0, waxing=True, a=pop, halo=0.9, dark_col="#2b3358", dark_a=0.92, edge=INK)
        else:
            u_ = clamp01((t - T_BIG_DARK) / 0.9)                     # 細い月が欠けきって、新月へ
            moon_disc(ctx, x_, BIG_MOON_Y, r_, 0.14 * (1.0 - u_), waxing=False, a=pop, dark_col="#2b3358", dark_a=0.92, edge=INK)
            lab = "細い月" if t < T_BIG_DARK + 0.45 else "新月"
        text(ctx, lab, x_ + 110, BIG_MOON_Y, 52, INK, align="left", alpha=pop)


BIG_MOON_Y = 790
BIG_MOONS = [(300, Sk("c1_new", 0.2), "新月", "new"), (860, Sk("c1_full", 0.3), "満月", "full"), (1420, Sk("c1_wane", 0.35), "", "wane")]
T_BIG_DARK = Sk("c1_wane", 0.72)


def walk_u(t, t0, wk, s_count=0.32, s_dark=0.12):
    """帰り道の進み u（0〜1）。歩けた1分（カウンターが増える分）は s_count 秒、歩けなかった1分は s_dark 秒かけて進む。
    カウンター「歩けた分」は1分ぶんを 0.3秒以上かけて数える（目で追える速さ。2026-10-29）"""
    if t <= t0:
        return 0.0
    el = t - t0
    for m in range(WALK - 1):
        d = s_count if wk.eff(m + 1) >= LINE else s_dark
        if el < d:
            return (m + el / d) / (WALK - 1)
        el -= d
    return 1.0


def walk_len(wk, s_count=0.32, s_dark=0.12):
    return sum(s_count if wk.eff(m + 1) >= LINE else s_dark for m in range(WALK - 1))


def sc_c1_lesson(ctx, t):
    t_b = Sk("c1_band") + 0.3
    u = walk_u(t, t_b, WSAMPLE)
    stage_single(ctx, t, WSAMPLE, u, pose="walk" if u > 0 else "stand", ga=fade(t, bd("c1_line") + 0.2, 0.4), sa=fade(t, Sk("c1_band") - 1.0, 0.4),
                 hi_bar=clamp01((t - Sk("c1_gauge", 0.1)) / 0.7) * out_fade(t, Ek("c1_gauge") + 0.3, 0.3), hi_line=clamp01((t - Sk("c1_gline", 0.1)) / 0.7) * out_fade(t, Ek("c1_gline") + 0.3, 0.3),
                 strip_title="帰り道の1時間（見本）", dark=lerp(0.52, 0.12, ease_in_out(u)))
    stk(ctx, t, "c1_line", "歩ける明るさ＝\n満月の夜の暗めの明るさ（仮定）", 60, 107, "yellow", size=44, off=0.2, tilt=-0.008)
    stk(ctx, t, "c1_band", "線を超えた時間＝歩けた時間", 1090, 338, "mint", size=44, off=0.3, until=Sk("c1_home", 0.0) - 0.2, tilt=0.008)
    stk(ctx, t, "c1_home", "1時間ぜんぶ青＝帰れた人", 1090, 338, "pink", fg=RED, size=48, off=0.3, tilt=0.008)


# ---- 中央値（1万人を歩けた分の小さい順に並べる）----
_CLS_SORTED = np.zeros(N, int)
_CLS_SORTED[N_ZERO:N_ZERO + N_MID] = 2
_CLS_SORTED[N_ZERO + N_MID:] = 1
GRID_MED = PeopleGrid(_CLS_SORTED, {0: DIM, 1: BLUE, 2: "#8fb4e6"}, {0: DIM, 1: BLUE, 2: "#8fb4e6"}, lit_cls=1, cx=LCX, y0=180.0, cell=5.0, seed=2)
T_MED0 = bd("c1_med")


def sc_c1_median(ctx, t):
    a = fade(t, T_MED0 + 0.1, 0.4)
    text(ctx, "小さい順に並べた1万人", LCX, GRID_MED.y0 - 44, 56, INK, alpha=a)
    nf = int(N * ease_in_out(clamp01((t - (T_MED0 + 0.3)) / 2.0)))
    GRID_MED.draw(ctx, nf, 0, a=a)
    text(ctx, "灰＝0分　青＝歩けた分あり", LCX, GRID_MED.y0 + GRID_MED.px + 70, 52, INK, alpha=a)
    # 旗（ちょうど真ん中）
    fa = fade(t, Sk("c1_med", 0.55), 0.4)
    if fa > 0.003:
        yf = GRID_MED.row_y(0.5)
        pen_line(ctx, GRID_MED.x0 - 20, yf, GRID_MED.x0 + GRID_MED.px + 20, yf, RED, seed=9, width=6, progress=clamp01((t - Sk("c1_med", 0.55)) / 0.8), alpha=fa)
        mini_sticky(ctx, "中央値", 150, yf, 48, "pink", fg=RED, a=fa, tilt=-0.03)
    stk(ctx, t, "c1_med", "歩けた分を、小さい順に並べた\nちょうど真ん中の値＝中央値", RX, 170, "yellow", size=44, off=0.2, tilt=-0.008)
    stk(ctx, t, "c1_med0", "中央値 0分", RX, 400, "pink", fg=RED, size=104, off=0.6, tilt=-0.012)
    stk(ctx, t, "c1_9of10", "10人に9人は\n1分も歩けていない", RX, 612, "mint", size=56, off=0.5, tilt=0.01)
    t_w = Sk("c1_wrong") + 0.2
    w_, h_ = stk(ctx, t, "c1_wrong", "予想\n悪い夜＝月のない夜\n月が出ていれば帰れる", RX, 815, "pink", size=44, off=0.2, tilt=0.0)
    if t > Sk("c1_wrong") + 1.4:
        pen_line(ctx, RX + 28, 815 + 58, RX + 478, 815 + 52, RED, seed=41, width=9, progress=clamp01((t - Sk("c1_wrong") - 1.4) / 0.7))


# ---- いちばん悪かった人 ----
T_RISE0 = Sk("c1_late") - 1.1                               # 月の出る時刻の図の枠
T_RISE1 = Sk("c1_wall") - 0.1
RISE_L = [15, 20, 26, 29]
RISE_AX0, RISE_AX1 = 1250.0, 1830.0                         # 時刻の軸（15時〜翌7時）
T_STEP0 = Sk("c1_step") - 1.1


def rise_x(h):
    return RISE_AX0 + (h - 15) * (RISE_AX1 - RISE_AX0) / 16.0


def rise_ys(i):
    return 150 + i * 62


def draw_rise_diagram(ctx, t, a=1.0):
    """右の列: 月の出る時刻（旧暦15・20・26・29日）。日がたつほど右へずれる"""
    text(ctx, "月の出る時刻", 1090, 78, 52, INK, align="left", alpha=a)
    for lab, h in (("夕", 18), ("夜中", 24), ("朝", 30)):
        text(ctx, lab, rise_x(h), 412, 48, PENCIL_T, alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(2.5)
        ctx.set_dash([6, 8])
        ctx.move_to(rise_x(h), 116)
        ctx.line_to(rise_x(h), 382)
        ctx.stroke()
        ctx.set_dash([])
    for i, L in enumerate(RISE_L):
        ra = fade(t, Sk("c1_late") - 0.3 + 0.55 * i, 0.3) * a
        yy = rise_ys(i)
        text(ctx, f"{L}日", 1095, yy, 48, INK, align="left", alpha=ra)
        hh = SD["rise_by_lday"][str(L)] / 60.0
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45 * ra))
        ctx.set_line_width(3)
        ctx.move_to(rise_x(15), yy)
        ctx.line_to(rise_x(31), yy)
        ctx.stroke()
        moon_row_item(ctx, rise_x(hh), yy, 20, L, a=ra)
    # 29日（この夜）を赤ペンの丸で
    pa = clamp01((t - Sk("c1_dawn", 0.2)) / 0.7)
    if pa > 0:
        pen_circle(ctx, rise_x(SD["rise_by_lday"]["29"] / 60.0), rise_ys(3), 44, 44, RED, seed=9, width=6, progress=pa, alpha=a)


def sc_c1_worst(ctx, t):
    t_rain = Sk("c1_wrain")
    clouds = lerp(0.0, 0.92, ease_in_out(clamp01((t - t_rain) / 1.4)))
    rain = t >= t_rain + 0.3
    kind = "night"
    dg0, dg1 = Sk("c1_east") - 0.3, Ek("c1_none") + 0.2
    diag = dg0 <= t <= dg1
    if diag:
        clouds, rain = 0.0, False
        if Sk("c1_sun") - 0.3 <= t < Sk("c1_none") - 0.2:
            kind = "day"
    elif t > dg1:
        clouds, rain = 0.92, True
    t_step = T_STEP0
    u = clamp01((t - Sk("c1_step")) / (Ek("c1_w0") - Sk("c1_step"))) if t >= Sk("c1_step") else 0.0
    wall = t >= Sk("c1_wall") - 0.1
    dark = 0.55 if t < t_step else lerp(0.55, 0.80, ease_in_out(clamp01((t - t_step) / 3.0)))
    m, e = stage_single(ctx, t, WWORST, u, pose="wall" if wall else "stand", umbrella=(t >= Sk("c1_w29")) and not wall, clouds=clouds, rain=rain, kind=kind,
                        person_a=fade(t, Sk("c1_wintro") - 0.2, 0.5), path_home=fade(t, Sk("c1_1h"), 0.5), dark=dark, ga=fade(t, T_STEP0, 0.4), sa=fade(t, T_STEP0, 0.4),
                        hi_bar=clamp01((t - Sk("c1_step", 0.6)) / 0.7), ruler_label=True)
    # 空の窓の図
    if diag:
        da = window(t, dg0, dg1, 0.3, 0.2)
        ctx.save()
        rrect(ctx, 60, SKY_Y0, 980, SKY_Y1 - SKY_Y0, 18)
        ctx.clip()
        if t < Sk("c1_sun") - 0.3:
            ctx.set_source_rgba(1, 1, 1, 0.65 * da)
            ctx.set_line_width(4)
            ctx.set_dash([4, 12])
            ctx.save()
            ctx.translate(565, 400)
            ctx.scale(335, 175)
            ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
            ctx.restore()
            ctx.stroke()
            ctx.set_dash([])
            pr = clamp01((t - (Sk("c1_east") + 0.3)) / (Dk("c1_east") + 0.3))
            th = math.pi * (1 - pr)
            moon_disc(ctx, 565 + 335 * math.cos(th), 400 - 175 * math.sin(th), 30, 0.55, waxing=True, a=da, halo=0.8)
            text(ctx, "東", 300, 305, 52, "#e9edff", alpha=da)
            text(ctx, "西", 880, 305, 52, "#e9edff", alpha=da)
        elif t < Sk("c1_none") - 0.2:
            sun_disc(ctx, 560, 285, 46, a=da)
            moon_disc(ctx, 690, 300, 30, 0.12, waxing=True, a=da, dark_col="#b9c7e6", dark_a=0.5, lit_col="#fff0a8", edge="#3b4a7a")
            text(ctx, "太陽", 560, 372, 48, INK, alpha=da)
            text(ctx, "細い月", 800, 372, 48, INK, alpha=da)
        else:
            text(ctx, "月はいない", 565, 300, 52, "#e9edff", alpha=da)
        ctx.restore()
    # 右の列の図: 月の出る時刻
    ra = window(t, T_RISE0, T_RISE1, 0.4, 0.3)
    if ra > 0.003:
        draw_rise_diagram(ctx, t, ra)
        sa = fade(t, Sk("c1_4h", 0.0) + 0.1, 0.4)
        if sa > 0.003:
            xs, xr = rise_x(SD["rise_by_lday"]["29"] / 60.0), 0
            ev = WORST["moon_events"]
            text(ctx, "夕方に沈む 17:42", 1090, 470, 48, INK, align="left", alpha=sa * ra)
            text(ctx, "翌朝4:34に昇る", 1090, 530, 48, INK, align="left", alpha=sa * ra)
    stk(ctx, t, "c1_w29", "旧暦29日・日記の天気は雨", 60, 107, "yellow", size=46, off=0.2, tilt=-0.008)


# ---- 同じ夜の人 262人 ----
def sc_c1_crowd(ctx, t):
    t0 = Sk("c1_260")
    ba = fade(t, bd("c1_260") + 0.2, 0.4)
    ctx.set_source_rgba(1, 1, 1, 0.82 * ba)
    rrect(ctx, 560, 48, 800, 118, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * ba))
    ctx.set_line_width(3)
    rrect(ctx, 560, 48, 800, 118, 16)
    ctx.stroke()
    text(ctx, "月が出ず雨の夜の人", 770, 107, 46, INK, alpha=ba)
    n_show = int(WORST_N * ease_in_out(clamp01((t - (t0 + 0.2)) / 2.4)))
    text(ctx, f"{WORST_N}人" if n_show >= WORST_N else "", 1170, 107, 84, RED, alpha=ba * fade(t, t0 + 2.6, 0.3))
    cols, rows = 22, 12
    for k in range(min(n_show, WORST_N)):
        r_, c_ = divmod(k, cols)
        tiny_person(ctx, 170 + c_ * 73.5, 262 + r_ * 58, 42, a=ba)


# ---- いちばん良かった人 ----
def sc_c1_best(ctx, t):
    u = clamp01((t - Sk("c1_bclear")) / (Ek("c1_bhour") - 0.3 - Sk("c1_bclear"))) if t >= Sk("c1_bclear") else 0.0
    sh = 330.0 * ease_in_out(clamp01((t - Sk("c1_bshadow")) / 1.6))
    mr = clamp01((t - Sk("c1_bround", 0.2)) / 0.8) * out_fade(t, Ek("c1_bround") + 0.2, 0.3)
    m, e = stage_single(ctx, t, WBEST, u, pose="walk" if u > 0 or t >= Sk("c1_bclear") else "stand", shadow=sh, person_a=fade(t, bd("c1_bintro") + 0.3, 0.5),
                        ga=fade(t, Sk("c1_bwinter") - 0.4, 0.4), sa=fade(t, Sk("c1_bwinter") - 0.4, 0.4),
                        hi_line=clamp01((t - Sk("c1_bline", 0.4)) / 0.7) * out_fade(t, Ek("c1_bline") + 0.3, 0.3))
    # 月に赤ペンの丸
    if mr > 0.003:
        alt = WBEST.alt[m]
        my = (SKY_Y1 - 22) - clamp01(alt / 90) * ((SKY_Y1 - 22) - (SKY_Y0 + 62)) - 6
        pen_circle(ctx, 60 + 0.60 * 980, my, 62, 62, RED, seed=5, width=6, progress=mr, alpha=1.0)
    stk(ctx, t, "c1_bwinter", "冬・満月のころ\n日記の天気は晴れ", 60, 107, "yellow", size=44, off=0.2, tilt=-0.008)


# ---- 左右に並べる（悪い人と良い人）----
def sc_c1_pair(ctx, t, answer=False):
    stage_half(ctx, t, "L", WWORST, 1.0, pose="wall", umbrella=False, clouds=0.92, rain=True, dark=0.78, ruler_label=True)
    stage_half(ctx, t, "R", WBEST, 0.9, pose="walk", shadow=300, ruler_label=True)
    if not answer:
        mini_sticky(ctx, "最悪", 190, 107, 56, "pink", fg=RED, a=fade(t, bd("c1_why") + 0.5, 0.3), tilt=-0.02)
        mini_sticky(ctx, "最良", 1120, 107, 56, "mint", a=fade(t, bd("c1_why") + 0.7, 0.3), tilt=0.02)
    else:
        t0 = Sk("c1_ans") + 1.0
        stk(ctx, t, "c1_ans", "最悪\n月が出ず、雨も降る夜", 60, 107, "pink", fg=RED, size=46, off=1.2, tilt=-0.01)
        stk(ctx, t, "c1_ans", "最良\n満月のころの、晴れた冬の夜", 990, 107, "mint", size=44, off=2.8, tilt=0.01)


# ---- 帯の上の月の高さ ----
def sc_c1_band(ctx, t):
    t0 = Sk("c1_reason") + 0.2
    pr = clamp01((t - t0) / (Dk("c1_reason") + 0.5))
    px0, px1 = 330.0, 1740.0
    for lane, (nm, key, y_top, vis, ttl) in enumerate((("best", "c1_reason", 150, True, "最良の夜"), ("worst", "c1_reason", 470, False, "最悪の夜"))):
        win = SD["window"][nm]
        mins, alt, EE = win["minutes"], win["alt"], win["E"]
        n = len(mins)
        a = fade(t, bd("c1_reason") + 0.1, 0.4)
        text(ctx, ttl, 60, y_top + 90, 46, INK, align="left", alpha=a)
        # 月の高さの線（0〜60度）
        yb = y_top + 190
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
        ctx.set_line_width(2.5)
        ctx.move_to(px0, yb)
        ctx.line_to(px1, yb)
        ctx.stroke()
        pts = []
        for k in range(n):
            xx = px0 + (px1 - px0) * k / (n - 1)
            hh = max(0.0, alt[k])
            pts.append((xx, yb - min(hh, 60) / 60 * 180))
        kk = int(clamp01(pr) * (n - 1))
        if kk >= 1:
            if lane == 0:
                ctx.set_source_rgba(*hexrgb(GOLD, 0.28 * a))
                _poly(ctx, [(pts[0][0], yb)] + pts[:kk + 1] + [(pts[kk][0], yb)])
                ctx.fill()
            ctx.set_source_rgba(*hexrgb("#c9951a" if lane == 0 else INK, 0.95 * a))
            ctx.set_line_width(7)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            _poly(ctx, pts[:kk + 1], close=False)
            ctx.stroke()
        # 帯（歩けた分を青く）
        by = yb + 16
        for k in range(n - 1):
            if k > kk:
                col = "#e9e3d3"
            else:
                col = BLUE if (vis and EE[k] >= LINE) else DIM
            ctx.set_source_rgba(*hexrgb(col, a))
            xa = px0 + (px1 - px0) * k / (n - 1)
            xb = px0 + (px1 - px0) * (k + 1) / (n - 1)
            ctx.rectangle(xa, by, xb - xa + 0.5, 46)
            ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.75 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(px0, by, px1 - px0, 46)
        ctx.stroke()
        if lane == 1:
            text(ctx, "月は地平線の下のまま", 1020, y_top + 70, 46, INK, alpha=a * fade(t, t0 + 1.0, 0.4))
    a2 = fade(t, bd("c1_reason") + 0.1, 0.4)
    text(ctx, "暮六つ", px0, 800, 46, INK, align="left", alpha=a2)
    text(ctx, "夜四つ", px1, 800, 46, INK, align="right", alpha=a2)
    text(ctx, "月の高さ", 60, 140, 40, PENCIL_T, align="left", alpha=a2 * 0)


# ---- ひと月の30個の丸 ----
BLACK_DAYS = [L for L in range(1, 31) if UP_SHARE[L] < 12]
BLUE_DAYS = [L for L in range(1, 31) if LDAY_P[L] > 0 and L <= 17 and L >= 10]


def month_xy(L):
    r_, c_ = divmod(L - 1, 10)
    return 190 + c_ * 171, 285 + r_ * 205


def sc_c1_month(ctx, t):
    a0 = fade(t, bd("c1_month") + 0.2, 0.4)
    text(ctx, "旧暦の1か月（30日）", 960, 130, 54, INK, alpha=a0)
    t_blk = Sk("c1_month", 0.45)
    t_blue = Sk("c1_8", 0.3)
    for L in range(1, 31):
        x_, y_ = month_xy(L)
        a = fade(t, bd("c1_month") + 0.3 + 0.07 * L, 0.3)                     # 30個の丸は 2秒あまりで並ぶ
        blk = fade(t, t_blk + 0.25 * BLACK_DAYS.index(L), 0.3) if L in BLACK_DAYS else 0.0     # 月のない夜は 1つずつ 0.25秒おき
        dim = 1.0 - 0.6 * fade(t, t_blue, 0.5) * (0 if L in BLUE_DAYS else 1)
        moon_disc(ctx, x_, y_, 50, lit_of_lday(L), waxing=L <= 15, a=a * dim * (1 - blk), dark_col="#2b3358", dark_a=0.92, edge=INK)
        if blk > 0.003:
            ctx.set_source_rgba(*hexrgb("#0b1030", 0.96 * blk * a * dim))
            ctx.arc(x_, y_, 50, 0, 2 * math.pi)
            ctx.fill()
        if L in BLUE_DAYS:
            bl = fade(t, t_blue + 0.25 * BLUE_DAYS.index(L), 0.3)
            if bl > 0.003:
                ctx.set_source_rgba(*hexrgb(BLUE, bl * a))
                ctx.set_line_width(9)
                ctx.arc(x_, y_, 60, 0, 2 * math.pi)
                ctx.stroke()
        text(ctx, f"{L}", x_, y_ + 78, 44, INK, alpha=a * dim)
    stk(ctx, t, "c1_fewer", "1時間ずっと届く夜は、もっと少ない", 960, 880, "pink", fg=RED, size=48, off=0.2, tilt=-0.01, align="center")


# ============================================================
# 第2章 満月のころなら、だれでも帰れる？
# ============================================================
def mini_people_row(ctx, x0, fy, n_blue, a=1.0, n=10, pitch=60, h=76, blue="#3a73c8", gray="#9aa0b6"):
    """10人の小さな人の列（左から n_blue 人が青・残りは灰）"""
    for k in range(n):
        tiny_person(ctx, x0 + k * pitch, fy, h, col=blue if k < n_blue else gray, a=a)


def sc_c2_title(ctx, t):
    title_hand(ctx, "問い2", RX, 150, 110, 8, fade(t, S("ch2") + T_TITLE + 0.3, 0.4))
    stk(ctx, t, "c2_intro", "満月のころの夜なら、\nだれでも、帰れる？", RX, 340, "yellow", size=52, off=1.4, tilt=-0.012)
    stk(ctx, t, "c2_yoso", "予想\n満月の夜なら、\nほとんど帰れる？", RX, 640, "pink", size=50, off=0.9, tilt=0.01)
    a = fade(t, Sk("c2_bright") - 0.9, 0.4)
    sky_window(ctx, 60, 250, 930, 640, t, kind="night", a=a)
    moon_disc(ctx, 495, 445, 110, 1.0, waxing=True, a=a, halo=0.9)


def sc_c2_moons(ctx, t):
    a = fade(t, bd("c2_15") + 0.2, 0.4)
    sky_window(ctx, 60, 330, 930, 720, t, kind="night", a=a)
    moon_disc(ctx, 300, 530, 110, 1.0, waxing=True, a=a * fade(t, Sk("c2_15") - 0.2, 0.4), halo=0.9)
    moon_disc(ctx, 700, 530, 110, 0.93, waxing=False, a=a * fade(t, Sk("c2_16") - 0.2, 0.4), halo=0.9)
    stk(ctx, t, "c2_15", "十五夜\n毎月の15日の夜", 113, 240, "yellow", size=44, off=0.5, tilt=-0.012)
    stk(ctx, t, "c2_16", "十六夜\n毎月の16日の夜", 513, 240, "mint", size=44, off=0.5, tilt=0.012)
    stk(ctx, t, "c2_lim", "十五夜は、満月とは限らない\n満月の瞬間は、計算では\n16日が一番多い", RX, 330, "pink", size=46, off=0.6, tilt=-0.01)
    stk(ctx, t, "c2_both", "どちらも、満月のころの夜", RX, 590, "mint", size=48, off=0.3, tilt=0.01)


# ---- 旧暦の日ごとの帰れた割合（棒グラフ）----
BX0, BX1, BY0, BY1 = 280.0, 1800.0, 790.0, 250.0           # 棒グラフの枠（左・右・0%の高さ・50%の高さ）
BPITCH = (BX1 - BX0) / 30
BMAX = 50.0


def bar_x(L):
    return BX0 + (L - 0.5) * BPITCH


def bar_top(p):
    return BY0 - (BY0 - BY1) * min(p, BMAX) / BMAX


T_BAR0 = Sk("c2_frame") - 1.05                              # 棒グラフの枠（軸・題・日にち）が出る
BAR_T = {}                                                  # L -> 棒が伸びる時刻（声に合わせる）
BAR_STEP = 0.25                                             # 束で伸びる棒は 1本ずつ 0.25秒おき（目で追える速さ）
for _L in range(1, 10):
    BAR_T[_L] = Sk("c2_zero", 0.25) + BAR_STEP * (_L - 1)
for _i, _L in enumerate((10, 11, 12, 13)):
    BAR_T[_L] = Sk("c2_rise", 0.3) + 0.5 * _i
BAR_T[15] = Sk("c2_15v", 0.55)
BAR_T[14] = Sk("c2_14v", 0.35)
BAR_T[16] = Sk("c2_16v", 0.55)
BAR_T[17] = Sk("c2_17", 0.4)
for _L in range(18, 31):
    BAR_T[_L] = Sk("c2_after", 0.1) + BAR_STEP * (_L - 18)


def sc_c2_bars(ctx, t):
    # 1万人 → 日ごとの束
    t_tiles = Sk("c2_tiles") - 0.3
    t_tiles_out = T_BAR0 - 0.2
    ta = fade(t, t_tiles, 0.3) * out_fade(t, t_tiles_out, 0.2)
    if ta > 0.003:
        stk(ctx, t, "c2_tiles", "旧暦の日ごとに分ける\n1つの日に、300人あまり", 960, 160, "yellow", size=52, off=-0.3, until=t_tiles_out, tilt=-0.01, align="center")
        for L in range(1, 31):
            r_, c_ = divmod(L - 1, 10)
            ar = fade(t, t_tiles + 0.5 + 0.07 * L, 0.3) * out_fade(t, t_tiles_out, 0.2)
            ctx.set_source_rgba(*hexrgb("#cfe0f7", ar))
            rrect(ctx, 130 + c_ * 172, 280 + r_ * 150, 150, 120, 14)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * ar))
            ctx.set_line_width(2.5)
            rrect(ctx, 130 + c_ * 172, 280 + r_ * 150, 150, 120, 14)
            ctx.stroke()
            text(ctx, f"{L}日", 205 + c_ * 172, 340 + r_ * 150, 44, INK, alpha=ar)
    # 棒グラフ
    fa = fade(t, T_BAR0, 0.4)
    if fa <= 0.003:
        return
    text(ctx, "帰れた人の割合", 280, 150, 56, INK, align="left", alpha=fa)
    ctx.set_source_rgba(1, 1, 1, 0.55 * fa)
    rrect(ctx, BX0 - 20, BY1 - 26, BX1 - BX0 + 40, BY0 - BY1 + 52, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * fa))
    ctx.set_line_width(3)
    ctx.move_to(BX0 - 10, BY0)
    ctx.line_to(BX1 + 10, BY0)
    ctx.stroke()
    text(ctx, "0%", BX0 - 22, BY0, 48, INK, align="right", alpha=fa)
    text(ctx, "50%", BX0 - 22, BY1, 48, INK, align="right", alpha=fa)
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.35 * fa))
    ctx.set_dash([8, 10])
    ctx.move_to(BX0 - 10, BY1)
    ctx.line_to(BX1 + 10, BY1)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "旧暦の日", 60, 842, 48, INK, align="left", alpha=fa)
    for L in (1, 5, 10, 15, 20, 25, 30):
        text(ctx, f"{L}", bar_x(L), 842, 48, INK, alpha=fa)
    for L in range(1, 31):
        p = LDAY_P[L]
        bu = ease_out(clamp01((t - BAR_T[L]) / 0.8))
        hh = (BY0 - bar_top(p)) * bu
        col = BLUE if L in (14, 15, 16) else "#7ea6e0"
        if hh > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * fa))
            ctx.rectangle(bar_x(L) - 20, BY0 - hh, 40, hh)
            ctx.fill()
        elif p == 0 and bu > 0.3:
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * fa))
            ctx.rectangle(bar_x(L) - 20, BY0 - 4, 40, 4)
            ctx.fill()
    # 十四夜・十五夜・十六夜の札と数字
    for L, nm, key, dx, yy in ((15, "十五夜", "c2_15v", 0, 312), (14, "十四夜", "c2_14v", -140, 270), (16, "十六夜", "c2_16v", 140, 495)):
        la = fade(t, Sk(key, 0.3), 0.3)
        if la > 0.003:
            lx, ly = bar_x(L) + dx, yy
            line2(ctx, (lx, ly + 24), (bar_x(L), bar_top(LDAY_P[L]) - 8), PENCIL_T, 3, a=0.7 * la)
            label(ctx, nm, lx, ly, 52, INK, a=la)
    stk(ctx, t, "c2_zero", "1〜9日は 0人", (bar_x(1) + bar_x(9)) / 2, 640, "pink", fg=RED, size=52, off=1.2, until=Sk("c2_15v", 0.0) - 0.2, tilt=-0.01, align="center")     # 2026-10-31 同じ絵は15秒まで
    stk(ctx, t, "c2_15v", "10人に4人", 300, 330, "yellow", size=56, off=0.55, tilt=-0.012, until=Sk("c2_44", 0.0) + 0.1)
    stk(ctx, t, "c2_44", "10人に4人", 300, 330, "yellow", size=56, off=0.0, tilt=-0.012)
    pr = fade(t, Sk("c2_44", 0.4), 0.4)
    if pr > 0.003:
        mini_people_row(ctx, 310, 560, 4, a=pr, pitch=46, h=64)
    stk(ctx, t, "c2_16v", "10人に2人", 1290, 560, "pink", fg=RED, size=56, off=0.6, tilt=0.012)
    if t > Sk("c2_half", 0.1):
        pa = clamp01((t - Sk("c2_half", 0.1)) / 0.6)
        arrow2(ctx, (bar_x(15) + 8, bar_top(LDAY_P[15]) - 4), (bar_x(16) + 30, bar_top(LDAY_P[16]) - 14), RED, w=6, a=pa, head=22)
        stk(ctx, t, "c2_half", "半分", 1300, 330, "pink", fg=RED, size=54, off=0.2, tilt=0.01)
    stk(ctx, t, "c2_winter", "冬の晴れた夜は、十六夜でも\n帰れた人がいる", 1100, 170, "mint", size=44, off=0.4, until=Sk("c2_best", 0.0) - 0.3, tilt=-0.01)
    stk(ctx, t, "c2_best", "問い1の最良の人も、冬の十六夜\n旧暦16日・冬・晴れ", 1100, 170, "mint", size=44, off=0.5, tilt=-0.01)
    stk(ctx, t, "c2_17", "100人に4人", 1330, 650, "yellow", size=50, off=0.5, tilt=0.01)
    w_, h_ = stk(ctx, t, "c2_wrong", "予想\n満月の夜なら、\nほとんど帰れる？", 300, 650, "pink", size=44, off=0.2, tilt=0.0)
    if t > Sk("c2_wrong") + 1.0:
        cross_mark(ctx, 300 + 182, 650, 52, a=1.0, p=clamp01((t - Sk("c2_wrong") - 1.0) / 0.7))


def sc_c2_look(ctx, t):
    stage_single(ctx, t, W15, 0.3, pose="stand", lookup=True, show_strip=False, ga=fade(t, bd("c2_look") + 0.2, 0.4),
                 hi_line=clamp01((t - Sk("c2_other", 0.3)) / 0.7) * out_fade(t, Ek("c2_other") + 0.3, 0.3), ruler_label=True)
    stk(ctx, t, "c2_look", "満月のころの夜", 60, 107, "yellow", size=48, off=0.3, tilt=-0.008)


T_PAIR0 = Sk("c2_pair") + 0.6
T_PAIR1 = Ek("c2_p16") + 0.3


def pair_u(t):
    return clamp01((t - T_PAIR0) / (T_PAIR1 - T_PAIR0))


def pair_state(t):
    """十五夜（左）の雲と暗さ: 理由1の雲で目盛りが線の下にもどる"""
    cl = lerp(0.0, 0.92, ease_in_out(clamp01((t - Sk("c2_r1", 0.4)) / 1.4)))
    dk = lerp(0.12, 0.72, ease_in_out(clamp01((t - Sk("c2_thick", 0.3)) / 2.0)))
    lm = 1.0 - ease_in_out(clamp01((t - (Sk("c2_cloud") + 0.5)) / 1.0))
    return cl, dk, lm


def sc_c2_pair(ctx, t):
    u = pair_u(t)
    stage_half(ctx, t, "L", W15, u, pose="walk" if 0 < u < 1 else "stand", shadow=160.0)
    stage_half(ctx, t, "R", W16, u, pose="walk" if 0 < u < 1 else "stand", shadow=0.0)
    stk(ctx, t, "c2_pair", "十五夜（毎月の15日）", 60, 107, "yellow", size=46, off=0.5, tilt=-0.008)
    stk(ctx, t, "c2_pair", "十六夜（毎月の16日）", 990, 107, "mint", size=46, off=0.8, tilt=0.008)


def sc_c2_pie(ctx, t):
    a = fade(t, bd("c2_half2") + 0.2, 0.4)
    cx, cy, r = 600, 540, 250
    sun_share = RES["diary_share"]["晴"] / 100.0
    th0 = -math.pi / 2
    th1 = th0 + 2 * math.pi * sun_share
    ctx.set_source_rgba(*hexrgb("#ffe08a", a))
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r, th0, th1)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#aab2c6", a))
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, r, th1, th0 + 2 * math.pi)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(4)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.stroke()
    sun_disc(ctx, cx + 120, cy - 20, 40, a=a)
    cloud(ctx, cx - 140, cy + 60, 210, "#7b839c", a)
    text(ctx, "晴れ", cx + 120, cy + 90, 54, INK, alpha=a)
    text(ctx, "雲・雨", cx - 140, cy + 160, 54, INK, alpha=a)
    stk(ctx, t, "c2_half2", "日記の天気\n晴れの日は、およそ半分", 1000, 400, "yellow", size=52, off=0.3, tilt=-0.01)
    stk(ctx, t, "c2_half2", "晴れの夜は目盛りが上がり\n曇りの夜は下がる", 1000, 640, "mint", size=48, off=1.0, tilt=0.01)


GREEN_K = "#4f8f6a"                                           # 雲の説明に出る別の町人の着物（十五夜の人とは別の人）


def sc_c2_cloudA(ctx, t):
    cl, dk, lm = pair_state(t)
    stage_single(ctx, t, WCLOUD, 0.3, pose="stand", clouds=cl, dark=lerp(0.10, 0.72, ease_in_out(clamp01((t - Sk("c2_thick", 0.3)) / 2.0))), kimono=GREEN_K,
                 show_strip=False, ga=fade(t, bd("c2_r1") + 0.2, 0.4), shadow=0.0)
    stk(ctx, t, "c2_r1", "雲が出た夜の人", 60, 107, "yellow", size=46, off=0.3, tilt=-0.008)


def sc_c2_cloud(ctx, t):
    cl, dk, lm = pair_state(max(t, Sk("c2_cloud")))
    stage_single(ctx, t, WCLOUD, 0.3, pose="stand", clouds=0.92, dark=0.72, kimono=GREEN_K, show_strip=False, level_mult=lm, shadow=0.0)
    stk(ctx, t, "c2_cloud", "雲が出れば、目盛りは線の下へ", 60, 107, "yellow", size=44, off=0.3, tilt=-0.008)


RISE2 = [(15, 380), (16, 500), (17, 620)]
R2X0, R2X1 = 360.0, 1720.0                                   # 16時〜21時


def r2x(h):
    return R2X0 + (h - 16) * (R2X1 - R2X0) / 5.0


RISE_H0, RISE_H1 = 16.5, 20.5


def rise_clock(t):
    """時刻の針の位置（時）。月は毎日遅れて昇る、の文の頭から、十六夜は遅い、の文の終わりまでで 16時半→20時半"""
    t0_, t1_ = Sk("c2_daily"), Ek("c2_later") - 0.3
    return RISE_H0 + (RISE_H1 - RISE_H0) * clamp01((t - t0_) / (t1_ - t0_))


def sc_c2_rise(ctx, t):
    a = fade(t, bd("c2_r2") + 0.2, 0.4)
    mini_sticky(ctx, "月の出る時刻", 960, 200, 54, "yellow", a=a, tilt=-0.012)
    for h in (17, 18, 19, 20):
        text(ctx, f"{h}時", r2x(h), 722, 48, INK, alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45 * a))
        ctx.set_line_width(2.5)
        ctx.set_dash([6, 8])
        ctx.move_to(r2x(h), 330)
        ctx.line_to(r2x(h), 680)
        ctx.stroke()
        ctx.set_dash([])
    # 時刻の針（2026-10-31 同じ絵は15秒まで）: 16時半から20時半へ進み、通ったところは夜の色に。針がその日の月の出を過ぎると、月が下から昇る
    hc = rise_clock(t)
    if hc > RISE_H0 + 1e-6:
        xc = r2x(hc)
        ctx.set_source_rgba(*hexrgb(NAVY, 0.13 * a))
        ctx.rectangle(r2x(RISE_H0), 330, xc - r2x(RISE_H0), 350)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(RED, 0.85 * a))
        ctx.set_line_width(6)
        ctx.move_to(xc, 318)
        ctx.line_to(xc, 692)
        ctx.stroke()
        ctx.arc(xc, 318, 11, 0, 2 * math.pi)
        ctx.fill()
    for i, (L, yy) in enumerate(RISE2):
        hh_ = SD["rise_by_lday"][str(L)] / 60.0
        up = ease_out(clamp01((hc - hh_) / 0.35)) if hc > hh_ else 0.0
        ra = up
        text(ctx, f"{L}日", 100, yy, 52, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45 * a))
        ctx.set_line_width(3)
        ctx.move_to(r2x(16), yy)
        ctx.line_to(r2x(21), yy)
        ctx.stroke()
        hh = SD["rise_by_lday"][str(L)] / 60.0
        moon_row_item(ctx, r2x(hh), yy + 46 * (1.0 - ra), 32, L, a=ra)
    la = clamp01((t - Sk("c2_later", 0.3)) / 0.7)
    if la > 0:
        arrow2(ctx, (r2x(SD["rise_by_lday"]["15"] / 60.0) + 50, 440), (r2x(SD["rise_by_lday"]["16"] / 60.0) - 40, 480), RED, w=6, a=la)
        mini_sticky(ctx, "十六夜は遅い", 1500, 440, 48, "pink", fg=RED, a=la, tilt=0.012)


def sc_c2_low(ctx, t):
    a = fade(t, bd("c2_low") + 0.2, 0.4)
    horizon = sky_window(ctx, 60, 200, 1860, 700, t, kind="night", a=a)

    def my(alt):
        return horizon - clamp01(alt / 30) * (horizon - 262)
    for L, x_, nm, key in ((15, 520, "十五夜", "c2_low"), (16, 1180, "十六夜", "c2_low")):
        al = ALT_DUSK[L]
        ma = a * fade(t, Sk(key) + (0.0 if L == 15 else 0.6), 0.4)
        ctx.save()
        rrect(ctx, 60, 200, 1800, 500, 18)
        ctx.clip()
        moon_disc(ctx, x_, my(al), 56, lit_of_lday(L, 0.0), waxing=L <= 15, a=ma, halo=0.9)
        ctx.restore()
        text(ctx, f"{nm}\n高さ{ihalf(al)}度", x_ + 90, my(al) - 40, 48, "#e9edff", align="left", alpha=ma)
    for x_, wd, key in ((520, 14, 0), (1180, 4, 1)):
        wa = fade(t, Sk("c2_weak") + 0.1 + 0.5 * key, 0.3)
        if wa > 0.003:
            arrow2(ctx, (x_ - 10, my(ALT_DUSK[15 if key == 0 else 16]) + 80), (x_ - 90, 790), GOLD, w=wd, a=wa, head=22 + wd)
    stk(ctx, t, "c2_weak", "低い月は、光が弱い", 960, 860, "yellow", size=54, off=0.3, tilt=-0.01, align="center")
    stk(ctx, t, "c2_low", "日が暮れたころ、月は\nまだ東の低いところ", 60, 107, "mint", size=44, off=0.3, tilt=-0.008)


def sc_c2_first(ctx, t):
    stage_half(ctx, t, "L", W15, 0.1, pose="stand", dark=0.12)
    stage_half(ctx, t, "R", W16, 0.1, pose="stand")
    stk(ctx, t, "c2_first", "十五夜", 60, 107, "yellow", size=48, off=0.1, until=Sk("c2_both2", 0.0) - 0.3, tilt=-0.008)
    stk(ctx, t, "c2_first", "十六夜：前半が暗い", 990, 107, "mint", size=48, off=0.4, until=Sk("c2_both2", 0.0) - 0.3, tilt=0.008)
    stk(ctx, t, "c2_both2", "理由1：雲", 360, 107, "yellow", size=50, off=0.2, until=Sk("c2_dep", 0.0) - 0.3, tilt=-0.012, align="center")
    stk(ctx, t, "c2_both2", "＋", 800, 107, "yellow", size=60, off=0.5, until=Sk("c2_dep", 0.0) - 0.3, tilt=0.0, align="center")
    stk(ctx, t, "c2_both2", "理由2：月の出の遅れ", 1300, 107, "mint", size=50, off=0.8, until=Sk("c2_dep", 0.0) - 0.3, tilt=0.012, align="center")
    stk(ctx, t, "c2_dep", "雲", 640, 107, "yellow", size=60, off=0.3, tilt=-0.012, align="center")
    stk(ctx, t, "c2_dep", "＋", 960, 107, "yellow", size=60, off=0.6, tilt=0.0, align="center")
    stk(ctx, t, "c2_dep", "月の出方", 1290, 107, "mint", size=60, off=0.9, tilt=0.012, align="center")


def sc_c2_ans(ctx, t):
    t0 = Sk("c2_ans")
    a0 = fade(t, bd("c2_ans") + 0.2, 0.4)
    stk(ctx, t, "c2_ans", "満月のころの夜 10人のうち\n帰れたのは4人（青）", 960, 190, "yellow", size=56, off=-0.5, tilt=-0.01, align="center")
    gr = fade(t, t0 + 1.0, 0.5)                                              # 10人が並びきってから（声の頭＋0.8秒）、帰れなかった6人が灰に（札「4人（青）」と合うように）
    for k in range(10):
        ak = fade(t, bd("c2_ans") + 0.3 + 0.17 * k, 0.3)
        blue = k < 4
        person(ctx, 215 + k * 165, 740, 380, t=t + 0.3 * k, pose="stand", kimono="#4d6fb3" if blue else (_mix("#4d6fb3", "#9aa0b6", gr)), a=ak)
        if blue:
            pass


def _mix(c0, c1, u):
    a, b = hexrgb(c0)[:3], hexrgb(c1)[:3]
    return "#%02x%02x%02x" % tuple(int(255 * (a[i] + (b[i] - a[i]) * u)) for i in range(3))


# ============================================================
# 第3章 冬と夏、帰れる夜が多いのはどちら？
# ============================================================
def sc_c3_title(ctx, t):
    title_hand(ctx, "問い3", RX, 150, 110, 12, fade(t, S("ch3") + T_TITLE + 0.3, 0.4))
    stk(ctx, t, "c3_intro", "冬と夏では、提灯なしで\n帰れる夜が多いのは、どちら？", RX, 340, "yellow", size=52, off=1.4, tilt=-0.012)
    stk(ctx, t, "c3_yoso", "予想\n夏のほうが、明るい？", RX, 620, "pink", size=50, off=0.9, tilt=0.01)


def season_rows():
    order = ["冬", "春", "夏", "秋"]
    key = {"冬": ("c3_w", 0.62), "春": ("c3_sa", 0.35), "夏": ("c3_s", 0.55), "秋": ("c3_sa", 0.95)}
    idx = {"冬": 0, "春": 1, "夏": 2, "秋": 3}
    rows = []
    for nm in order:
        k_, f_ = key[nm]
        i = idx[nm]
        rows.append(lk.Row(nm, SEASON_P[i] / 100.0, t_label=bd("c3_cal") + 0.5 + 0.12 * len(rows), t_value=Sk(k_, f_), color=BLUE if nm in ("冬", "夏") else "#7ea6e0", line=ID[k_],
                           text=f"100人に{ihalf(SEASON_P[i])}人"))
    return rows


SEAS_ROWS = season_rows()
SEAS = lk.LadderPanel("帰れた人の割合", SEAS_ROWS, box=(1000, 130, 1860, 640), t_frame=bd("c3_cal") + 0.4, vmax=0.12, label_size=52, val_size=48, title_size=52, fade=0.4,
                      title_line=ID["c3_w"], plus=False, arrows=False)


def sc_c3_seasons(ctx, t):
    stk(ctx, t, "c3_cal", "冬＝12〜2月", 60, 200, "yellow", size=52, off=0.3, tilt=-0.01)
    stk(ctx, t, "c3_cal", "夏＝6〜8月", 60, 320, "pink", size=52, off=0.9, tilt=0.01)
    a = fade(t, Sk("c3_2500") - 0.6, 0.4)
    text(ctx, "1つの季節に 2500人ほど", LCX, 470, 48, INK, alpha=a)
    for k, nm in enumerate(("冬", "春", "夏", "秋")):
        r_, c_ = divmod(k, 2)
        ar = fade(t, Sk("c3_2500") - 0.4 + 0.25 * k, 0.3)
        cx_, cy_ = 270 + c_ * 390, 590 + r_ * 170
        ctx.set_source_rgba(*hexrgb("#cfe0f7", ar))
        rrect(ctx, cx_ - 170, cy_ - 65, 340, 130, 14)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * ar))
        ctx.set_line_width(2.5)
        rrect(ctx, cx_ - 170, cy_ - 65, 340, 130, 14)
        ctx.stroke()
        text(ctx, nm, cx_, cy_, 64, INK, alpha=ar)
    SEAS.draw(ctx, t, 1.0)
    stk(ctx, t, "c3_5", "冬は、夏の5倍ほど", RX, 705, "pink", fg=RED, size=56, off=0.2, tilt=-0.01)
    w_, h_ = stk(ctx, t, "c3_wrong", "予想\n夏のほうが、明るい？", RX, 845, "pink", size=44, off=0.2, tilt=0.0)
    if t > Sk("c3_wrong") + 1.0:
        cross_mark(ctx, RX + 215, 845, 48, a=1.0, p=clamp01((t - Sk("c3_wrong") - 1.0) / 0.7))


T3_0 = Sk("c3_see") + 0.8


def u3(t):
    return clamp01((t - T3_0) / 34.0)


def sc_c3_pair(ctx, t, rainy=False):
    u = u3(t)
    stage_half(ctx, t, "L", WWIN, u, pose="walk", shadow=200.0)
    stage_half(ctx, t, "R", WTSU, u, pose="wall", clouds=0.92, rain=True, dark=0.7, ruler_label=True)
    stk(ctx, t, "c3_see", "冬の、満月のころの夜\n旧暦14日・日記の天気は晴れ", 60, 107, "yellow", size=44, off=0.3, tilt=-0.008)
    stk(ctx, t, "c3_see", "梅雨の、満月のころの夜\n1788年6月17日（旧暦5月14日）・雨", 990, 107, "mint", size=44, off=0.6, tilt=0.008)


def sc_c3_clear(ctx, t):
    a = fade(t, bd("c3_w7") + 0.2, 0.4)
    stk(ctx, t, "c3_w7", "日記の天気（10日のうち）", 960, 170, "yellow", size=54, off=-0.4, tilt=-0.01, align="center")
    for row, (nm, n_blue, key, yy) in enumerate((("冬", 7, "c3_w7", 380), ("夏", 4, "c3_s4", 560))):
        text(ctx, nm, 250, yy, 72, INK, alpha=a)
        for k in range(10):
            ak = a * fade(t, Sk(key, 0.0) + 0.25 * k, 0.25)                    # 1つずつ 0.25秒おき
            cx_ = 480 + k * 125
            ctx.set_source_rgba(*hexrgb(BLUE if k < n_blue else DIM, ak))
            ctx.arc(cx_, yy, 44, 0, 2 * math.pi)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * ak))
            ctx.set_line_width(3)
            ctx.arc(cx_, yy, 44, 0, 2 * math.pi)
            ctx.stroke()
            if k < n_blue:
                sun_disc(ctx, cx_, yy, 12, a=ak * 0.0)
    text(ctx, "青＝晴れ　灰＝曇り・雨", 960, 720, 52, INK, alpha=a)


def sc_c3_geo0(ctx, t):
    a = fade(t, bd("c3_r2") + 0.2, 0.4)
    stk(ctx, t, "c3_r2", "理由の2つ目：満月の高さ", 960, 170, "yellow", size=54, off=0.3, tilt=-0.01, align="center")
    sun_disc(ctx, 330, 520, 70, a=a)
    ctx.set_source_rgba(*hexrgb("#4f86c8", a))
    ctx.arc(960, 520, 100, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#4fa66a", a))
    ctx.arc(930, 500, 48, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(4)
    ctx.arc(960, 520, 100, 0, 2 * math.pi)
    ctx.stroke()
    moon_disc(ctx, 1590, 520, 56, 1.0, waxing=True, a=a, halo=0.7, dark_col="#46507a")
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * a))
    ctx.set_line_width(3)
    ctx.set_dash([10, 12])
    ctx.move_to(410, 520)
    ctx.line_to(1520, 520)
    ctx.stroke()
    ctx.set_dash([])
    for nm, x_ in (("太陽", 330), ("地球", 960), ("満月", 1590)):
        text(ctx, nm, x_, 680, 54, INK, alpha=a)
    stk(ctx, t, "c3_opp", "満月は、太陽と反対がわ", 960, 790, "pink", size=54, off=0.2, tilt=0.01, align="center")


def sky_arcs(ctx, x0, a, sun_alt, moon_alt, sun_a=1.0, moon_a=1.0, hi_moon=0.0, base=700):
    """観測する人の空（半円）。太陽の通り道（橙の点線）と満月の通り道（金）。高さは角度に比例"""
    cx, rx = x0 + 435, 315
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * a))
    ctx.set_line_width(4)
    ctx.move_to(x0 + 60, base)
    ctx.line_to(x0 + 810, base)
    ctx.stroke()
    for alt, col, aa, dash, wd in ((sun_alt, "#ff9f2e", sun_a, [4, 12], 6), (moon_alt, "#d6a41a", moon_a, [], 6 + 7 * hi_moon)):
        if aa <= 0.003:
            continue
        ry = alt / 90.0 * 420
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a * aa))
        ctx.set_line_width(wd)
        ctx.set_dash(dash)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.save()
        ctx.translate(cx, base)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1, math.pi, 2 * math.pi)
        ctx.restore()
        ctx.stroke()
        ctx.set_dash([])
        if col == "#ff9f2e":
            sun_disc(ctx, cx, base - ry, 22, a=a * aa, rays=False)
            text(ctx, "太陽", cx, base - ry - 54, 48, INK, alpha=a * aa)
        else:
            moon_disc(ctx, cx, base - ry, 24, 1.0, waxing=True, a=a * aa, halo=0.6, dark_col="#46507a")
            text(ctx, "満月", cx, base - ry - 54, 48, INK, alpha=a * aa)


def sc_c3_geo(ctx, t):
    a = fade(t, bd("c3_wlow") + 0.2, 0.4)
    for x0, nm, sun_alt, moon_alt, k_s, k_m in ((60, "冬", 31, 78, "c3_wlow", "c3_whigh"), (990, "夏", 78, 31, "c3_shigh", "c3_slow")):
        ctx.set_source_rgba(1, 1, 1, 0.55 * a)
        rrect(ctx, x0, 190, 870, 580, 18)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
        ctx.set_line_width(3)
        rrect(ctx, x0, 190, 870, 580, 18)
        ctx.stroke()
        text(ctx, nm, x0 + 70, 250, 64, INK, alpha=a)
        hi = clamp01((t - Sk(k_m, 0.1)) / 0.6)
        sky_arcs(ctx, x0, a, sun_alt, moon_alt, sun_a=fade(t, Sk(k_s, 0.0), 0.4), moon_a=fade(t, Sk(k_m, 0.0), 0.4), hi_moon=hi)
    # 月の高さ・光
    stk(ctx, t, "c3_41", "冬 41度", 495, 840, "yellow", size=64, off=0.35, tilt=-0.012, align="center")
    stk(ctx, t, "c3_24", "夏 24度", 1425, 840, "pink", fg=RED, size=64, off=0.35, tilt=0.012, align="center")
    for x0, wd, nm, key in ((60, 16, "強い光", 0), (990, 5, "弱い光", 1)):
        wa = fade(t, Sk("c3_weak", 0.1 + 0.5 * key), 0.3)
        if wa > 0.003:
            alt = 78 if key == 0 else 31
            arrow2(ctx, (x0 + 150, 700 - alt / 90 * 420 + 60), (x0 + 120, 690), GOLD, w=wd, a=wa, head=20 + wd)
            text(ctx, nm, x0 + 110, 735, 48, INK, align="center", alpha=wa)


E_ROWS = []
for _nm, _i, _k, _f in (("冬", 0, "c3_wline", 0.5), ("春", 1, "c3_between", 0.3), ("夏", 2, "c3_sline", 0.5), ("秋", 3, "c3_between", 0.8)):
    E_ROWS.append(lk.Row(_nm, SEASON_E[_i], t_label=bd("c3_avg") + 0.05 + 0.03 * len(E_ROWS), t_value=Sk(_k, _f), color=BLUE if SEASON_E[_i] >= LINE else "#7ea6e0", line=ID[_k], text=None))
E_PANEL = lk.LadderPanel("満月のころの月明かり（平均）", E_ROWS, box=(1000, 150, 1860, 720), t_frame=bd("c3_avg") + 0.0, vmax=0.10, label_size=52, val_size=44, title_size=48, fade=0.4,
                         title_line=ID["c3_avg"], plus=False, arrows=False, fmt=lambda v: "")


def sc_c3_e(ctx, t):
    stk(ctx, t, "c3_avg", "満月のころ（旧暦13〜16日）の\n帰り道の月明かり（平均）", 60, 200, "yellow", size=44, off=0.2, tilt=-0.008)
    E_PANEL.draw(ctx, t, 1.0)
    g = E_PANEL.layout()
    xl = g["track_x"] + g["track_w"] * (LINE / E_PANEL.vmax)
    la = fade(t, E_PANEL.t_frame + 0.1, 0.4)
    ctx.set_source_rgba(*hexrgb(RED, 0.95 * la))
    ctx.set_line_width(5)
    ctx.set_dash([14, 9])
    ctx.move_to(xl, 230)
    ctx.line_to(xl, 700)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "歩ける線", xl, 762, 52, RED, alpha=la)
    stk(ctx, t, "c3_tsu2", "梅雨の夜の人は、\n雲に月をかくされる", 60, 520, "pink", size=48, off=0.3, tilt=0.01)


def sc_c3_final(ctx, t):
    u = clamp01(u3(t) + 0.0)
    stage_half(ctx, t, "L", WWIN, 1.0, pose="stand", shadow=250.0, path_home=1.0, px=60 + 0.37 * 870)
    stage_half(ctx, t, "R", WSUM, 1.0, pose="wall", ruler_label=True)
    stk(ctx, t, "c3_tsu2", "夏の晴れた夜の人：\n雲がないのに、月が低い", 990, 107, "mint", size=44, off=0.2, until=Sk("c3_w2", 0.0) + 0.0, tilt=0.008)
    stk(ctx, t, "c3_w2", "冬の夜の人：\n影を落として家に着いた", 60, 107, "yellow", size=44, off=0.2, tilt=-0.008)
    stk(ctx, t, "c3_diff", "季節で、これほど差が出る", 990, 107, "mint", size=44, off=0.2, until=Sk("c3_ans", 0.0) - 0.3, tilt=0.008)
    stk(ctx, t, "c3_ans", "答えは、冬\n晴れが多く、満月も高い", 990, 107, "pink", fg=RED, size=44, off=0.5, tilt=0.008)


# ============================================================
# 第4章 まとめ
# ============================================================
def sc_c4_answers(ctx, t):
    t0 = S("ch4") + 2.3
    for s_, x_, col, k in (("最悪＝月が出ず雨の夜", 330, "pink", 0), ("満月でも10人に4人", 960, "yellow", 1), ("冬は夏の5倍ほど", 1590, "mint", 2)):
        mini_sticky(ctx, s_, x_, 230, 46, col, a=fade(t, t0 + 0.25 * k, 0.4), tilt=-0.015 + 0.015 * k)
    stk(ctx, t, "c4_0", f"100人に{P_ALL}人", 960, 500, "pink", fg=RED, size=124, off=1.2, tilt=-0.012, align="center")


def sc_c4_walk(ctx, t):
    # まとめでは1時間の帯を数え直さない（60分を0.3秒ずつ数えると18秒かかる）。帯は青で埋まった形で出し、町人は歩きつづける
    u = 1.0
    stage_single(ctx, t, WWIN, u, pose="walk", shadow=260.0, ga=fade(t, bd("c4_1") + 0.2, 0.4), sa=fade(t, bd("c4_1") + 0.2, 0.4), strip_title="帰り道の1時間")
    stk(ctx, t, "c4_1", "満月のころの、冬の晴れた夜", 60, 107, "yellow", size=48, off=0.2, tilt=-0.008)


def sc_c4_close(ctx, t):
    """締めの問い（c4_2）・注意書きの札（c4_3）。終了画面の前に読める"""
    q = fade(t, Sk("c4_2") + 0.1, 0.4)
    if q > 0.003:
        mini_sticky(ctx, "あなたなら、\n提灯なしで、\n出かけますか？", 1430, 200, 52, "yellow", a=q, tilt=-0.02)
        person(ctx, 1235, 880, 420, t=t, pose="stand", lookup=True, a=q)
        moon_disc(ctx, 1530, 440, 58, 1.0, waxing=True, a=q, halo=0.9, dark_col="#46507a")
    nt = fade(t, Sk("c4_3", 0.1), 0.4)
    if nt > 0.003:
        mini_sticky(ctx, WIDE_NOTE, 490, 470, 52, "pink", a=nt, tilt=0.012)


# ============================================================
# 終了画面（最後の約10秒）・区切り・全体
# ============================================================
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"
LCX_E, RCX_E = 490, 1430
WIDE_NOTE = f"もっと暗くても歩けるとすると、\n100人に{WIDE_P}人ほど"           # 線を 0.02 lx にしたとき（まとめの札で1回だけ。声では言わない）


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
    return [("提灯なしで帰れたのは", f"100人に{P_ALL}人ほど", "yellow", INK, -0.010),
            ("満月のころの夜でも", f"10人に{ihalf(LDAY_P[15] / 10)}人ほど", "pink", RED, 0.008),
            ("冬に帰れたのは、夏の", f"{ihalf(SEASON_P[0] / SEASON_P[2])}倍ほど", "mint", INK, -0.008)]


def sc_end(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.4, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "江戸の夜道を、1万人で歩かせたら", LCX_E, 162, 44, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=60)
    t9 = T_ES + 0.5
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


CARD_POS = {1: (960, 300), 2: (960, 300), 3: (960, 300), 4: (960, 560)}
CARD_HOLD = {1: 2.5, 2: 2.5, 3: 2.5, 4: 2.0}              # 章カードを出す秒数（問いのカードは 9字 → 文字数÷8＋1秒 ＝ 2.1秒以上読める）
T_TITLE = 2.4                                             # 章の題字の場面は、章カードが消えてから（章の頭から 2.4秒）


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
EC_LEFT = ("いちばん悪い夜と良い夜", "満月のころの夜")
EC_RIGHT = ("冬と夏の夜", "帰りやすいのは？")
EC_FADE = 0.35                                          # Eyecatch は t1 から 0.35秒で消える。次の章カードと文字が重ならないよう、消え終わりを問い3の始まりにそろえる
EC = lk.Eyecatch(T_RS0, EC_LEFT, EC_RIGHT, dur=(T_RS1 - T_RS0) - EC_FADE) if len(REST) == 1 else None

# ---- 場面の並び ----
SC_START = {}


def _sc(name, t0, t1, fn, first=False):
    SC_START[name] = t0
    scene(name, t0, t1, fn, first)


_sc("open", 0.0, bd("c0_drew"), sc_open, first=True)
_sc("walk9", bd("c0_drew"), T_GRID0, sc_walk9)
_sc("grid", T_GRID0, bd("c0_next"), sc_grid)
_sc("tags", bd("c0_next"), S("ch1") - 0.3, sc_tags)
_sc("c1_title", S("ch1") + T_TITLE, bd("c1_moon"), sc_c1_title)
_sc("c1_moon", bd("c1_moon"), bd("c1_kuji"), sc_c1_moon)
_sc("c1_rules", bd("c1_kuji"), bd("c1_cal"), sc_c1_rules)
_sc("c1_phases", bd("c1_cal"), bd("c1_line"), sc_c1_phases)
_sc("c1_lesson", bd("c1_line"), bd("c1_med"), sc_c1_lesson)
_sc("c1_median", bd("c1_med"), bd("c1_wintro"), sc_c1_median)
_sc("c1_worst", bd("c1_wintro"), bd("c1_260"), sc_c1_worst)
_sc("c1_crowd", bd("c1_260"), bd("c1_bintro"), sc_c1_crowd)
_sc("c1_best", bd("c1_bintro"), bd("c1_why"), sc_c1_best)
_sc("c1_why", bd("c1_why"), bd("c1_reason"), lambda c, t: sc_c1_pair(c, t, False))
_sc("c1_band", bd("c1_reason"), bd("c1_month"), sc_c1_band)
_sc("c1_month", bd("c1_month"), bd("c1_ans"), sc_c1_month)
_sc("c1_ans", bd("c1_ans"), S("ch2") - 0.3, lambda c, t: sc_c1_pair(c, t, True))
_sc("c2_title", S("ch2") + T_TITLE, bd("c2_15"), sc_c2_title)
_sc("c2_moons", bd("c2_15"), bd("c2_tiles"), sc_c2_moons)
_sc("c2_bars", bd("c2_tiles"), bd("c2_look"), sc_c2_bars)
_sc("c2_look", bd("c2_look"), bd("c2_pair"), sc_c2_look)
_sc("c2_pair", bd("c2_pair"), bd("c2_r1"), sc_c2_pair)
_sc("c2_cloudA", bd("c2_r1"), bd("c2_half2"), sc_c2_cloudA)
_sc("c2_pie", bd("c2_half2"), bd("c2_cloud"), sc_c2_pie)
_sc("c2_cloud", bd("c2_cloud"), bd("c2_r2"), sc_c2_cloud)
_sc("c2_rise", bd("c2_r2"), bd("c2_low"), sc_c2_rise)
_sc("c2_low", bd("c2_low"), bd("c2_first"), sc_c2_low)
_sc("c2_first", bd("c2_first"), bd("c2_ans"), sc_c2_first)
_sc("c2_ans", bd("c2_ans"), (T_RS0 - 0.3) if EC else DUR, sc_c2_ans)
_sc("c3_title", S("ch3") + T_TITLE, bd("c3_cal"), sc_c3_title)
_sc("c3_seasons", bd("c3_cal"), bd("c3_see"), sc_c3_seasons)
_sc("c3_pair1", bd("c3_see"), bd("c3_w7"), sc_c3_pair)
_sc("c3_clear", bd("c3_w7"), bd("c3_rainy"), sc_c3_clear)
_sc("c3_pair2", bd("c3_rainy"), bd("c3_r2"), sc_c3_pair)
_sc("c3_geo0", bd("c3_r2"), bd("c3_wlow"), sc_c3_geo0)
_sc("c3_geo", bd("c3_wlow"), bd("c3_avg"), sc_c3_geo)
_sc("c3_e", bd("c3_avg"), bd("c3_tsu2"), sc_c3_e)
_sc("c3_final", bd("c3_tsu2"), S("ch4") - 0.3, sc_c3_final)
_sc("c4_answers", S("ch4") + 1.9, bd("c4_1"), sc_c4_answers)
_sc("c4_walk", bd("c4_1"), bd("c4_2"), sc_c4_walk)
_sc("c4_close", bd("c4_2"), T_ES, sc_c4_close)
_sc("end", T_ES, DUR + 2.0, sc_end)


def draw(ctx, t, sub=True):
    lf.spread(ctx)
    ea = EC.alpha(t) if (EC and T_RS0 <= t < T_RS1) else 0.0
    tint = 0.14 * (1.0 - ea) * (1.0 - fade(t, T_ES + 0.1, 0.4))
    if tint > 0.003:
        ctx.set_source_rgba(*hexrgb(NAVY, tint))
        ctx.rectangle(0, 0, lf.W, lf.H)
        ctx.fill()
    if ea < 0.5:
        draw_scenes(ctx, t)
        overlays(ctx, t)
    if ea > 0.003:
        EC.draw(ctx, t)
    if sub:
        lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・区切りの足音）
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


BELLS = [Sk("c0_res", 0.5), Sk("c1_med0", 0.6), BAR_T[15], BAR_T[16], SEAS_ROWS[0].t_value, SEAS_ROWS[2].t_value, E_ROWS[0].t_value, E_ROWS[2].t_value]


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
        ("01_0.0s", "① 0.0秒: 問い・左に月夜／右に闇夜の町人", 0.0),
        ("02_2.5s", "② 2.5秒", 2.5),
        ("03_5.0s", "③ 5.0秒", 5.0),
        ("04_open_lantern", "④ 提灯に火がともる（0章）", Sk("c0_lan") + 2.0),
        ("05_open_kuji", "⑤ くじの箱から札（右ページ・1万マスの場面）", Sk("c0_10k") + 1.6),
        ("06_open_walk9", "⑥ 九夜の人（目盛りは線の下）", Sk("c0_dark") + 1.6),
        ("07_result", "⑦ 結果の数字（100人に7人）", Sk("c0_res") + 3.6),
        ("08_conditions", "⑧ 条件の札（仮定を囲む）", Sk("c0_assume") + 2.2),
        ("09_tags", "⑨ 3つの問い", Sk("c0_q2") + 1.2),
        ("09b_ch1_phases", "⑨b 問い1: 旧暦の月の形を1つずつ大きく（新月・満月・細い月→新月）", Sk("c1_wane") + 5.2),
        ("10_ch1_median", "⑩ 問い1: 中央値 0分", Sk("c1_9of10") + 1.8),
        ("11_ch1_worst", "⑪ 問い1: いちばん悪い夜の人（傘・雨・月は地平線の下）", Sk("c1_w0") + 1.5),
        ("12_ch1_best", "⑫ 問い1: いちばん良い夜の人（影・満月・1時間まるごと）", Sk("c1_bhour") + 1.2),
        ("13_ch1_crowd", "⑬ 問い1: 同じ夜の人 262人", Sk("c1_nolone") + 0.4),
        ("13b_ch2_zero", "⑬b 問い2: 棒が0の日に「1〜9日は 0人」", Sk("c2_zero") + 2.6),
        ("14_ch2_bars", "⑭ 問い2: 十五夜と十六夜（棒グラフ）", Sk("c2_half") + 1.6),
        ("15_ch2_pair", "⑮ 問い2: 十五夜と十六夜を並べて歩かせる", Sk("c2_p16") + 1.4),
        ("16_ch2_ans", "⑯ 問い2の答え: 10人のうち4人", Sk("c2_ans") + 1.8),
        ("17a_ec_start", "⑰a 区切り: 始め", REST_STILLS[0]),
        ("17b_ec_mid", "⑰b 区切り: 亀が真ん中", REST_STILLS[1]),
        ("17c_ec_end", "⑰c 区切り: 終わり", REST_STILLS[2]),
        ("18_ch3_bars", "⑱ 問い3: 季節ごとの割合（冬は夏の5倍）", Sk("c3_5") + 1.4),
        ("19_ch3_pair", "⑲ 問い3: 冬の人と梅雨の人を並べる", Sk("c3_tsu") + 0.6),
        ("19b_ch3_summer", "⑲b 問い3: 冬の人と夏の晴れの人（月が低く目盛りは線の下）", Sk("c3_tsu2") + 2.0),
        ("19c_ch2_cloud", "⑲c 問い2: 雲の説明は別の町人（十五夜の人ではない）", Sk("c2_cloud") + 2.2),
        ("19d_ch2_rise", "⑲d 問い2: 時刻の針が進み、十五夜→十六夜→17日と月が遅れて昇る", Sk("c2_later") + 3.0),
        ("20_ch3_geo", "⑳ 問い3: 冬は満月が高く、夏は低い", Sk("c3_24") + 1.2),
        ("21_ch3_e", "㉑ 問い3: 満月のころの月明かりと歩ける線", Sk("c3_between") + 2.2),
        ("22_summary", "㉒ まとめ: 3つの答え・100人に7人", Sk("c4_0") + 3.0),
        ("23_end", "㉓ 終了画面", min(DUR - 0.5, Sk("c4_sub", 0.0) + 1.5)),
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
    """読みの確認。read_aloud が AivisSpeech を起動するので、--fake-voice のときは読みを作らず、文だけ並べる"""
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
    dl, fi = SC_FAST.get(scene_name, (SC_DELAY, SC_IN))
    return max(SC_START[scene_name] + dl + fi, own_t + d)


# 冒頭の1万マスの枠だけは visual_lag（声の0.5秒前）の例外: 0〜30秒は間を足せず、前の文（c0_dark）の終わりまで前の場面を残すため。
#   代わりに「声の文の頭までにそろう」を scene_checks で確かめる（CUE_GRID0）
CUE_GRID0 = lk.Cue("1万マスの枠（読み方・マス）", "frame", T_GRID0, rd("grid", T_GRID0, 0.25), ID["c0_10k"])
ALL_CUES = [
    lk.Cue("1万マス 帰れた人が光る", "value", T_LIGHT0, T_LIGHT1, ID["c0_res"]),
    lk.Cue("箱「100人に7人」", "value", Sk("c0_res", 0.5), Sk("c0_res", 0.5) + 0.3, ID["c0_res"]),
    lk.Cue("目盛り（明るさと歩ける線）の枠", "frame", T_W9G, rd("walk9", T_W9G, 0.4), ID["c0_dark"]),
    lk.Cue("1時間の帯の枠", "frame", Sk("c0_left") + 0.3, rd("walk9", Sk("c0_left") + 0.3, 0.4), ID["c0_dark"]),
    lk.Cue("並べた1万人（中央値）の枠", "frame", T_MED0 + 0.1, rd("c1_median", T_MED0 + 0.1, 0.4), ID["c1_med"]),
    lk.Cue("中央値 0分", "value", Sk("c1_med0", 0.6), Sk("c1_med0", 0.6) + 0.3, ID["c1_med0"]),
    lk.Cue("目盛り（見本）の枠", "frame", bd("c1_line") + 0.2, rd("c1_lesson", bd("c1_line") + 0.2, 0.4), ID["c1_gauge"]),
    lk.Cue("帯（見本）の枠", "frame", Sk("c1_band") - 1.0, rd("c1_lesson", Sk("c1_band") - 1.0, 0.4), ID["c1_band"]),
    lk.Cue("月の出る時刻の図の枠", "frame", T_RISE0 + 0.1, rd("c1_worst", T_RISE0 + 0.1, 0.4), ID["c1_late"]),
    lk.Cue("最悪の人の目盛りと帯の枠", "frame", T_STEP0, rd("c1_worst", T_STEP0, 0.4), ID["c1_step"]),
    lk.Cue("最良の人の目盛りと帯の枠", "frame", Sk("c1_bwinter") - 0.4, rd("c1_best", Sk("c1_bwinter") - 0.4, 0.4), ID["c1_bround"]),
    lk.Cue("月の高さの帯の枠", "frame", bd("c1_reason") + 0.1, rd("c1_band", bd("c1_reason") + 0.1, 0.4), ID["c1_reason"]),
    lk.Cue("棒グラフ（日ごと）の枠", "frame", T_BAR0, rd("c2_bars", T_BAR0, 0.4), ID["c2_frame"]),
    lk.Cue("棒 十五夜", "value", BAR_T[15], BAR_T[15] + 0.8, ID["c2_15v"]),
    lk.Cue("棒 十四夜", "value", BAR_T[14], BAR_T[14] + 0.8, ID["c2_14v"]),
    lk.Cue("棒 十六夜", "value", BAR_T[16], BAR_T[16] + 0.8, ID["c2_16v"]),
    lk.Cue("棒 17日", "value", BAR_T[17], BAR_T[17] + 0.8, ID["c2_17"]),
] + SEAS.cues() + E_PANEL.cues()

# ============================================================
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
CARD_LINES = {ln for t_ in CARD_TITLES for ln in t_.split("\n")}
WARNS = []


def _allowed_nums():
    ok = set(float(x) for x in range(0, 61)) | {100.0, 262.0, 300.0, 679.0, 1788.0, 2500.0, 10000.0, 1849.0}
    ok |= {float(P_ALL), float(WIDE_P), float(N_ALL), float(WORST_N)}
    return ok


def first_seen(frames, pred):
    for f in frames:
        if any(pred(e[0], e) for e in f[1]):
            return f[0]
    return None


STILL_MAX = 15.0                 # 同じ絵は15秒まで（2026-10-31 ユーザーOK）
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


SCENE_MIN = 3.0                 # 場面・グラフは最低3秒出す
COUNT_SEC = 0.3                 # カウンター（歩けた分）は 1分ぶんを 0.3秒以上かけて数える


def pace_problems():
    """場面の長さ（3秒未満）と、文の途中で場面が替わる所（2026-10-29 ユーザー指摘「映像の切り替わりが早すぎる」）"""
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


def counter_problems(frames, label_re=r"歩けた分 (\d+)分", sec=COUNT_SEC):
    """カウンターが速すぎる所: 同じカウンターが続けて出ているあいだ、t1〜t2 で増えた分が (t2−t1)/sec ＋1 を超えるもの"""
    runs, cur = [], []
    for t_, ents in frames:
        v = [int(m_.group(1)) for e in ents for m_ in [_re.fullmatch(label_re, e[0])] if m_]
        if v:
            cur.append((t_, v[0]))
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    bad = []
    for r_ in runs:
        worst = None
        for i in range(len(r_)):
            for j in range(i + 1, len(r_)):
                dt, dv = r_[j][0] - r_[i][0], r_[j][1] - r_[i][1]
                if dt > 6.0:
                    break
                over = dv - (dt / sec + 1.0)
                if over > 1e-9 and (worst is None or over > worst[0]):
                    worst = (over, r_[i], r_[j])
        if worst:
            _o, (ta, va), (tb, vb) = worst
            bad.append(f"{_ts(ta)}〜{_ts(tb)} {va}→{vb}分（{(tb - ta) / max(1, vb - va):.2f}秒/分）")
    return bad


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    checks = []
    WARNS.clear()

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def WARN(msg):
        WARNS.append(msg)
        print("  注意:", msg)
    # ---- 台本の読み込み ----
    A(f"台本: 章は5つ（0〜4）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 5 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    A("台本: 声と字幕に〔 〕が1つも混ざらない", not any(("〔" in v[1] or "〕" in v[1]) for v in LINES.values()))
    title_line = next(ln for ln in NARR_PATH.read_text(encoding="utf-8").splitlines() if ln.startswith("題名案1:"))
    A(f"題名「{QTXT}」の言葉が台本の題名案1と同じ（句読点をのぞく。サムネと同じ言葉）", QTXT.replace("、", "") in title_line.replace("、", ""))
    V = lambda name, val, exp, tol: checks.append((name, float(val), float(exp), tol))
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:]) if S(b) < 70]
    A(f"台本: 冒頭（0〜70秒）の文と文の間は 0.3秒前後（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし", all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch2"))
    sil = [(g, GAP_SEC[g]) for g in GAP_NOTE]
    A(f"台本: 無音はどこも10秒以内（{sil}）・最初の無音は第2章の終わり（{min(S(g) for g in GAP_NOTE):.1f}秒）", all(v <= 10 for _g, v in sil))
    n_rest = len(REST)
    A(f"区切り: 台本の「（無音 4秒・区切り。…）」は {n_rest} か所・長さ {T_RS1 - T_RS0:.1f}秒（約4秒）", n_rest == 1 and abs((T_RS1 - T_RS0) - 4.0) < 0.01)
    A(f"区切り: 問い2のあと・問い3の前（{_ts(T_RS0)}〜{_ts(T_RS1)}）・章は5つのまま（{len(CHAPS)}章・chapters {len(tl.chapters)}）・区切りは章に入っていない",
      n_rest == 1 and T_RS0 >= E(ID["c2_ans"]) - 1e-6 and abs(T_RS1 - S("ch3")) < 1e-6 and len(CHAPS) == 5 and len(tl.chapters) == 5
      and not any("区切り" in t_ or "ここまで" in t_ for t_ in CH_TITLES) and all(abs(t0_ - T_RS0) > 1e-6 for t0_, _ in tl.chapters))
    A(f"区切り: 動画の真ん中あたり（{(T_RS0 + T_RS1) / 2 / DUR:.1%} のところ）・声の行なし", 0.35 <= (T_RS0 + T_RS1) / 2 / DUR <= 0.75 and not any(T_RS0 - 1e-6 <= s_ < T_RS1 for s_, *_r in tl._lines))
    A(f"区切り: 左は「ここまで」＋「{EC_LEFT[0]}」「{EC_LEFT[1]}」・右は「ここから」＋「{EC_RIGHT[0]}」「{EC_RIGHT[1]}」", EC.texts() == {"ここまで", "ここから", *EC_LEFT, *EC_RIGHT})
    xs_ = [EC.X0 + (EC.X1 - EC.X0) * EC._u(T_RS0 + u_) for u_ in np.arange(0.0, 4.0001, 0.05)]
    A(f"区切り: 亀は左ページ（x {xs_[0]:.0f}）から右ページ（x {xs_[-1]:.0f}）へ歩く・足音 {len(EC.step_times())} 個", xs_[0] < 400 and xs_[-1] > 1500 and len(EC.step_times()) >= 10)
    nums40 = set()
    for it in tl.items:
        if isinstance(it, lf.Line) and E(it.id) < 40:
            nums40 |= set(_re.findall(r"\d+人に\d+人|\d[\d,]*", split_reading(it.text)[0]))
    A(f"台本: 冒頭40秒（言い終わる文）の声の数字は3個以内（{sorted(nums40)}）", len(nums40) <= 3)
    t_res0, t_res1 = Sk("c0_res"), Ek("c0_res")
    A(f"冒頭の結果の数字（100人に{P_ALL}人）の声の始まりは {t_res0:.1f}秒（本番の声は30秒以内・偽の声は余裕を見て29.5秒以内）", t_res0 <= (29.5 if FAKE else 30.0))
    # 結果の数字が声で言われる時刻（文の頭〜終わり）を記録
    A(f"冒頭の結果の数字の文は 0:{t_res0:04.1f}〜0:{t_res1:04.1f}（40秒以内には収まる）", t_res1 <= 40.0)
    A(f"台本: 結果の数字は問い1より前（0章の中）", t_res1 < S("ch1"))
    # ---- 声の数字 = data.json ----
    exp = [("c0_res", f"100人に{P_ALL}人"), ("c1_med0", "0分"), ("c1_9of10", f"10人に{ihalf(MC['zero'] / 10)}人"), ("c1_260", "260人ほど"), ("c1_4h", "4時半"),
           ("c1_month", f"10夜に{ihalf(len(BLACK_DAYS) / 3)}夜"), ("c1_8", f"{len(BLUE_DAYS)}日間"), ("c2_tiles", "300人あまり"), ("c2_15v", f"10人に{ihalf(LDAY_P[15] / 10)}人"),
           ("c2_44", f"10人に{ihalf(LDAY_P[15] / 10)}人"), ("c2_16v", f"10人に{ihalf(LDAY_P[16] / 10)}人"), ("c2_17", f"100人に{ihalf(LDAY_P[17])}人"),
           ("c3_2500", "2500人ほど"), ("c3_w", f"100人に{ihalf(SEASON_P[0])}人"), ("c3_s", f"100人に{ihalf(SEASON_P[2])}人"), ("c3_5", f"{ihalf(SEASON_P[0] / SEASON_P[2])}倍"),
           ("c3_sa", f"100人に{ihalf(SEASON_P[1])}人ほど"), ("c3_w7", f"10日に{ihalf(RES['moon_profile']['by_season']['0']['clear_final'] / 10)}日"),
           ("c3_s4", f"10日に{ihalf(RES['moon_profile']['by_season']['2']['clear_final'] / 10)}日"), ("c3_41", f"{ihalf(SEASON_ALT[0])}度"), ("c3_24", f"{ihalf(SEASON_ALT[2])}度"),
           ("c4_0", f"100人に{P_ALL}人"), ("c2_half2", "およそ半分")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    sa_ = txt("c3_sa")
    A(f"秋の数字（声は 100人に{ihalf(SEASON_P[3])}人ほど）: {sa_}", f"100人に{ihalf(SEASON_P[3])}人ほど" in sa_)
    A("声の「月の終わり 29日・雨」は data.json の最悪の人（旧暦29日・雨雪・歩けた分0）と同じ・「4時半」は月の出 翌04:34",
      WORST["lday"] == 29 and WORST["sky"] == "雨雪" and WORST["walkable_min"] == 0 and any(k == "rise" and v.endswith("04:34") for v, k in WORST["moon_events"]))
    A("声の「冬の、満月のころの、晴れた夜」は data.json の最良の人（冬・旧暦16日・晴・60分）と同じ", BEST["season"].startswith("冬") and BEST["sky"] == "晴" and BEST["walkable_min"] == 60 and BEST["lday"] == 16)
    pp = SD["people"]
    A("場面の町人: 九夜（旧暦9日・晴・歩けた分0）／十五夜（15日・晴・60分）／十六夜（16日・晴・前半は線の下・後半は線の上）／冬（新暦12〜2月・旧暦14日・晴・60分）／梅雨（1788-06-17・旧暦5月14日・雨）",
      pp["n9"]["lday"] == 9 and pp["n9"]["walkable_min"] == 0 and pp["n15"]["lday"] == 15 and pp["n15"]["walkable_min"] == 60 and pp["n16"]["lday"] == 16
      and pp["n16"]["series"]["E"][0] < LINE <= pp["n16"]["series"]["E"][-1] and pp["winter14"]["lday"] == 14 and pp["winter14"]["season"].startswith("冬") and pp["winter14"]["walkable_min"] == 60
      and pp["tsuyu"]["date"] == "1788-06-17" and pp["tsuyu"]["kyureki"] == "5月14日" and pp["tsuyu"]["sky"] == "雨雪" and not pp["tsuyu"]["sky_visible"])
    sm = pp["summer"]
    A(f"夏の晴れの人: {sm['date']}（旧暦{sm['kyureki']}・{sm['season']}・晴・空が見える・歩けた分0・月の高さ {sm['moon_alt_at_depart']}〜{sm['moon_alt_at_arrive']}度・60分とも歩ける線の下 最大 {max(sm['series']['E']):.3f} lx）",
      sm["season"].startswith("夏") and sm["lday"] in (14, 15) and sm["sky"] == "晴" and sm["sky_visible"] and sm["walkable_min"] == 0 and max(sm["series"]["E"]) < LINE)
    A(f"町人の大きさ: 身長 {PERSON_H}px ＝ 画面の高さの {PERSON_H / lf.H:.0%}（3分の1 {lf.H / 3:.0f}px 以上）・単独の場面は {PERSON_H}px", PERSON_H >= lf.H / 3)
    A(f"歩ける線 {LINE} lx ＝ 目盛りの 25%（上端 {G_MAX} lx）・満月のいちばん良い人の照度は 0.15〜0.19 lx", abs(LINE / G_MAX - 0.25) < 1e-9 and 0.15 < max(BEST["series"]["E"]) < 0.2)
    pb = GRID_OPEN.check(N_ALL) + GRID_MED.check(N_HOME)
    A(f"1万マス: 光るマスの数がデータと同じ（帰れた {N_ALL:,}／並べた1万人の青 {N_HOME}）: {pb}", not pb and N_ALL == N_HOME or (not pb and abs(N_ALL - N_HOME) <= 1))
    A(f"1万マス: 100×100 ＝ 1万・灰（0分）{N_ZERO:,}＋途中 {N_MID}＋帰れた {N_HOME} ＝ {N_ZERO + N_MID + N_HOME:,}", N_ZERO + N_MID + N_HOME == N)
    A(f"月のない日（月が出ていない日）は 30日のうち {len(BLACK_DAYS)} 日（10夜に4夜）・歩ける日は {len(BLUE_DAYS)} 日（8日間）", len(BLACK_DAYS) == 12 and len(BLUE_DAYS) == 8)
    sx = [r.text for r in SEAS.rows]
    A(f"季節の棒の値の文字は data.json（冬・春・夏・秋）: {sx}", sx == [f"100人に{ihalf(SEASON_P[i])}人" for i in range(4)])
    probs = SEAS.layout_problems() + E_PANEL.layout_problems()
    A(f"棒の枠の配置の問題: {probs}", not probs)
    # ---- 絵は声より先に・答えは声に合わせて ----
    # ---- 場面の切りかえの速さ（2026-10-29）----
    short_sc, mid_sc = pace_problems()
    A(f"場面の長さ: どの場面も {SCENE_MIN:.0f}秒以上（短い場面 {short_sc}）・最短 {min(t1_ - t0_ for _n, t0_, t1_, *_r in SCENES):.1f}秒", not short_sc)
    A(f"場面は、その場面で話している文の終わりまで消さない（文の途中で替わる所 {len(mid_sc)} か所 {mid_sc[:3]}）", not mid_sc)
    A(f"第1章からは、場面の切りかえの前の間が {SCENE_GAP}秒以上（次の場面は声の約0.6秒前にそろう）: 足りない {[k for k in SCENE_KEYS if S(ID[k]) - E(PREV_LINE[ID[k]]) < SCENE_GAP - 1e-6]}",
      all(S(ID[k]) - E(PREV_LINE[ID[k]]) >= SCENE_GAP - 1e-6 for k in SCENE_KEYS))
    A(f"冒頭の1万マスの枠は、前の文（c0_dark）を言い終えてから出て、声の文の頭 {Sk('c0_10k'):.2f}秒までにそろう（{CUE_GRID0.ready:.2f}秒。0〜30秒は間を足せないので 0.5秒前の例外）",
      E(ID["c0_dark"]) - 1e-6 <= T_GRID0 and CUE_GRID0.ready <= Sk("c0_10k") + 1e-6)
    A(f"カウンターの1時間: 見本の人は {walk_len(WSAMPLE):.1f}秒（c1_band の頭〜c1_home の終わり {Ek('c1_home') - Sk('c1_band') - 0.3:.1f}秒に収まる）・最良の人は {(Ek('c1_bhour') - 0.3 - Sk('c1_bclear')) / WALK:.2f}秒/分",
      walk_len(WSAMPLE) <= Ek("c1_home") - Sk("c1_band") - 0.3 and (Ek("c1_bhour") - 0.3 - Sk("c1_bclear")) / WALK >= COUNT_SEC)
    steps_ = [BAR_T[L + 1] - BAR_T[L] for L in list(range(1, 9)) + list(range(18, 30))]
    A(f"棒グラフ: 束で伸びる棒（1〜9日・18〜30日）は 1本 {min(steps_):.2f}秒おき（0.25秒以上）・全体 {BAR_T[9] - BAR_T[1] + 0.8:.1f}秒／{BAR_T[30] - BAR_T[18] + 0.8:.1f}秒（2秒以上）",
      min(steps_) >= 0.25 - 1e-9 and BAR_T[9] - BAR_T[1] + 0.8 >= 2.0 and BAR_T[30] - BAR_T[18] + 0.8 >= 2.0)
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件（最も先: {min(r[3] for r in rows_):+.1f}秒）{[b[0] for b in bad[:4]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]

        def _pad_card(fr_):
            cd_ = [e for e in fr_[1] if e[0] in CARD_LINES]
            if not cd_:
                return fr_
            box_ = ("章カード", min(e[1] for e in cd_) - 50, min(e[2] for e in cd_) - 40, max(e[3] for e in cd_) + 50, max(e[4] for e in cd_) + 40, cd_[0][5])
            return (fr_[0], [e for e in fr_[1] if e[0] not in CARD_LINES] + [box_], *fr_[2:])
        pairs = lk.text_box_overlaps([_pad_card(f_) for f_ in frames], skip=[(T_ES, T_ES + 0.6)])
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）。章カードも付せんの下地ごと数えた", "字幕の行（「字幕: …」）の箱を含めて調べた"])
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
        l0_ = {e[0] for e in f0[1]}
        A(f"冒頭: 0秒目から左に「月夜」・右に「闇夜」の町人（札が出ている）", {"月夜", "闇夜"} <= l0_)
        A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
        # 結果の数字が画面に出る時刻
        t_big = first_seen(frames, lambda s_, e: s_ == f"100人に{P_ALL}人")
        A(f"画面の「100人に{P_ALL}人」は声の文の頭 {t_res0:.1f}秒の後（初出 {t_big}秒）・文の終わり {t_res1:.1f}秒より前", t_big is not None and t_res0 <= t_big <= t_res1 + 0.5)
        # 答えの数字が声より先に出ていないか
        tokens = [(f"100人に{P_ALL}人", "c0_res"), ("中央値 0分", "c1_med0"), ("10人に4人", "c2_15v"), ("10人に2人", "c2_16v"), ("100人に4人", "c2_17"), ("冬 41度", "c3_41"), ("夏 24度", "c3_24"),
                  (f"{WORST_N}人", "c1_260"), ("冬は、夏の5倍ほど", "c3_5"), (f"1万人のうち {N_ALL:,}人", "c0_res")]
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
        A(f"画面に出る数字は、すべて data.json の値（の四捨五入）か、目もり・日付などの閉じた値: 余分 {len(extra)}個 {list(extra)[:5]}", not extra)
        short_t = _check_long_mod().short_texts(frames)
        for a_, b_, s_, need_ in short_t[:12]:
            print(f"  札の表示時間 {_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒／要 {need_:.1f}秒 「{s_[:30]}」")
        A(f"札の表示時間: 画面の文字は「文字数÷8＋1秒」以上出る（字幕・カウンターは除く）: 足りない {len(short_t)} 件", not short_t)
        sp_ = still_spans()
        long_ = [f"{_ts(a_)}〜{_ts(b_)}（{b_ - a_:.1f}秒）" for a_, b_ in sp_ if b_ - a_ > STILL_MAX + 1e-6]
        print(f"  同じ絵の長い区間（字幕なし・0.5秒ごと・{STILL_THR:.1%}以上で動いた）: " + "、".join(f"{_ts(a_)}〜{_ts(b_)} {b_ - a_:.1f}秒" for a_, b_ in sp_[:6]))
        A(f"同じ絵は{STILL_MAX:.0f}秒まで（最長 {sp_[0][1] - sp_[0][0]:.1f}秒）: 超える区間 {long_}", not long_)
        cbad = counter_problems(frames)
        A(f"カウンター「歩けた分」は 1分ぶんを {COUNT_SEC}秒以上かけて数える: 速すぎる所 {cbad}", not cbad)
        expo = sorted({e[0] for t_, e in allt if _re.search(r"10\^|\d[eE][+\-]?\d|乗", e[0]) and not e[0].startswith("字幕: ")})
        A(f"指数表記を画面に出さない: {expo}", not expo)

        def has(a_, b_, keys):
            fr = [f for f in frames if a_ <= f[0] < b_]
            miss = [k for k in keys if first_seen(fr, lambda s_, e, k=k: s_ == k) is None]
            return not miss, miss
        okk, miss = has(0, S("ch1"), ["月夜", "闇夜", "夜と天気を、くじで選ぶ", "歩ける線", "明るさ", "月の高さ", "帰り道の1時間", "条件", "場所: 日本橋あたり", "旧暦9日・晴れ", "青＝帰れた　1マス＝1人", f"100人に{P_ALL}人", "問い1"])
        A(f"0章: 付せん・町人の場面・目盛り・1万マス・条件・3つの問いの札が出る（欠け {miss}）", okk)
        okk, miss = has(S("ch1"), S("ch2"), ["問い1", "予想", "旧暦", "歩ける線", "明るさ", "小さい順に並べた1万人", "中央値", "中央値 0分", "月の出る時刻", "旧暦の1か月（30日）", "最悪", "最良", "歩けた分 0分", "歩けた分 60分"])
        A(f"1章: 題字・予想・旧暦・目盛り・中央値・月の出る時刻・最悪の人と最良の人・30個の丸が出る（欠け {miss}）", okk)
        okk, miss = has(S("ch2"), S("ch3"), ["問い2", "十五夜", "十六夜", "十四夜", "帰れた人の割合", "旧暦の日", "10人に4人", "10人に2人", "月の出る時刻"])
        A(f"2章: 題字・十五夜と十六夜・棒グラフ・月の出る時刻が出る（欠け {miss}）", okk)
        okk, miss = has(S("ch3"), S("ch4"), ["問い3", "冬＝12〜2月", "夏＝6〜8月", "帰れた人の割合", "冬", "夏", "春", "秋", "満月のころの月明かり（平均）", "歩ける線", "冬 41度", "夏 24度"])
        A(f"3章: 題字・季節の棒・冬と夏の月の高さ・月明かりの棒と歩ける線が出る（欠け {miss}）", okk)
        rs_in = [f for f in frames if T_RS0 + 0.5 <= f[0] <= T_RS1 - 0.05]
        rs_txt = {e[0] for f in rs_in for e in f[1]}
        A(f"区切りの間は、EC.texts() の文字だけが出ている: {sorted(rs_txt)}", bool(rs_in) and rs_txt <= EC.texts())
        ec_e = [e for f in rs_in for e in f[1] if e[0] in EC.texts()]
        A(f"区切りの文字は 40px 以上（最小 {min((e[5] for e in ec_e), default=0):.0f}px）・左は x<940・右は x>980（のどをまたがない）",
          bool(ec_e) and min(e[5] for e in ec_e) >= 40 and all((e[3] < 940 if e[0] in ("ここまで", *EC_LEFT) else e[1] > 980) for e in ec_e))
        # 一人に寄る場面の部品（目盛り・歩ける線・帯・月の高さ）が、町人の場面に必ずそろう
        for nm, key, tq in (("九夜", "c0_dark", T_GRID0 - 0.8), ("最悪の人", "c1_w0", Ek("c1_w0") - 0.3), ("最良の人", "c1_bhour", Ek("c1_bhour") - 0.3)):
            fr = min(frames, key=lambda f: abs(f[0] - tq))
            lbl = {e[0] for e in fr[1]}
            miss = [k for k in ("明るさ", "歩ける線", "帰り道の1時間", "月の高さ") if k not in lbl]
            A(f"{nm}の場面（{_ts(fr[0])}）: 町人・空の月・目盛りと歩ける線・1時間の帯の文字がそろう（欠け {miss}）", not miss)
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if not e[0].startswith("字幕: ") and (e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936)]
        for t_, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t_)} 「{s_}」")
        A(f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", not out_es)
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        A(f"終了画面: 登録のお願い（「よければ」{Sk('c4_sub'):.1f}秒〜）の{Sk('c4_sub') - T_ES:.1f}秒前から最後まで（{DUR - T_ES:.1f}秒・YouTube の終了画面は最低5秒なので6〜8秒）。締めの問い・注意書き・札は、その前の場面に出る",
          0.2 <= Sk("c4_sub") - T_ES <= 1.0 and 6.0 <= DUR - T_ES <= 8.0 and T_ES > E(ID["c4_3"]) - 1e-6)
        pre = [e[0] for f in frames if Sk("c4_2") <= f[0] < T_ES for e in f[1]]
        A("まとめ: 締めの問い「あなたなら、提灯なしで、出かけますか？」と札が、終了画面の前（問いの文〜注意書きの文）に読める",
          all(x in pre for x in ("あなたなら、", "提灯なしで、", "出かけますか？", WIDE_NOTE.splitlines()[0], WIDE_NOTE.splitlines()[-1])))
        end_t = min(DUR - 0.2, Sk("c4_sub", 0.0) + 1.5)
        n_end = {e[0] for f in frames if abs(f[0] - end_t) < 0.13 for e in f[1]}
        A(f"終了画面に 答え3つ（{[r[1] for r in end_rows()]}）・登録の付せんが出る", all(r[1] in n_end for r in end_rows()) and "チャンネル登録・高評価" in n_end)
        A(f"まとめ: 札「{WIDE_NOTE.splitlines()[-1]}」は終了画面より前（{_ts(S('ch4'))}〜{_ts(T_ES)} のあいだ）に出て、終了画面には出ない（声では言わない）",
          any(e[0] == WIDE_NOTE.splitlines()[-1] for f in frames if S("ch4") <= f[0] < T_ES for e in f[1])
          and not any(e[0] == WIDE_NOTE.splitlines()[-1] for f in frames if f[0] >= T_ES + 0.3 for e in f[1]) and "14" not in "".join(tl.clip(i).text for i in LINES))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK" + (f"（注意 {len(WARNS)} 件）" if WARNS else ""))
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
        for nm_, t0_, t1_, *_r in SCENES:
            print(f"場面 {nm_}: {t0_:.1f}-{t1_:.1f}")
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
    frames = lk.scan_frames(draw, DUR, timeline=tl)
    import pickle
    (OUT / "frames_real.pkl").write_bytes(pickle.dumps(frames))              # 本番の声の文字の箱（check-long の札の表示時間の点検が読む）
    scene_checks(frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
