"""エアコン暖房、30分の外出は つけっぱなしと こまめに消す、どっちが電気を使わない？ 同じ部屋2つで1万回くらべる。— 2026-10-13 作成（公開予定 10/18）

モデル（部屋1つ・暖房だけ・外の気温は一定）
  部屋: 空気（＋家具）と、壁・床・天井のかたまり（熱をためる所）の2つの温度で表す（RC モデル。
        ISO 13790 の 5R1C を、表面の節点を空気とかたまりの間の直列の抵抗にまとめて2つにしたもの）。
        熱の通り道: 空気 → 外（窓とすきま風・換気）、空気 ↔ かたまり（内側の表面）、かたまり → 外（壁を通る）。
        熱の逃げやすさ（床1m²・温度差1℃あたり）は 1.6〜5.0 W のでたらめ。1.6〜2.7 は平成11年基準の熱損失係数の基準値の幅、
        それより大きい所は古い家・すきま風の多い部屋を仮定した。そのうち空気から直接逃げる割合は 35〜65%。
        かたまりの熱容量は床1m²あたり 110〜260 kJ/K（ISO 13790 の軽い〜重いつくり）。
        空気と内側の表面のつながり 3.45 W/m²K × 表面積（床の4.5倍）、表面とかたまりのつながり 9.1 W/m²K × 床の2.5〜3倍（ISO 13790）。
        空気の節点の熱容量は、空気（天井高2.5m）＋すぐ温まる家具など 5〜20 kJ/K（床1m²あたり・仮定）。
  エアコン（インバーター・ヒートポンプ）: 国の住宅の省エネ計算（建築研究所「エネルギー消費性能計算プログラム（住宅版）」
        第四章 第三節 ルームエアコンディショナー Ver.03）の式をそのまま使う。
        部屋の広さから定格・最大の暖房能力と定格の効率を決め（付録A）、消費電力は「出している熱 ÷ 最大能力」と外の気温の
        4次式（容量可変型の係数）で決まる。全力に近いほど、熱1あたりの電気が多い（効率が落ちる）。外が寒いほど、最大の熱も効率も下がる。
        風量の補正 0.8、外が5℃未満で湿度80%以上なら霜取りの補正 0.77 も同じ式どおりに入れる。
        温め方: 設定温度より低ければ、届くかぎり（最大能力まで）熱を出して空気を設定温度に戻す。設定温度に届いたら、保つだけの熱を出す。
        計算: 20秒ごとに熱を一定とみなし、2つの温度は行列の指数関数で厳密に進める。温め直しの最中だけは1歩をさらに40に分ける。
  1回ぶん: 外の気温 −2〜12℃、湿度 50〜95%、設定温度 20〜24℃、広さ 10〜23m²（6〜14畳）、断熱、熱容量、エアコンの効率の区分を
        でたらめに選び、まったく同じ部屋を2つ用意する。どちらも設定温度で落ち着いた所から出かける。
        つけっぱなし: 出かけている間も設定温度のまま。こまめに消す: 出かけている間は切り、帰ったらつける。
        くらべる電気: 「出かけていた分のために使った電気」。つけっぱなしは留守のあいだの電気。こまめに消すは、帰ってから
        ふだんより多く使った電気の合計（温め直し）。帰って3時間までは1歩ずつ計算し、その先（冷えた壁などが元に戻るまで）は
        閉じた形の積分で足す（tail）。それ以外の時間はどちらもふだんどおりなので、この差が全部の電気の差になる。
  本編: 外出30分で1万回。 ひねり: 外出を10分〜6時間（対数で一様）のでたらめにした別の1万回と、部屋ごとの「境目の時間」。

問い: 「エアコン暖房、30分の外出は つけっぱなしと こまめに消す、どっちが安い？」 A つけっぱなし ／ B こまめに消す ／ C ほぼ同じ
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1回ごとの差 ΔE = （こまめに消すの電気）−（つけっぱなしの電気）。つけっぱなしのほうが少ない回の割合を p、
      差を「つけっぱなしで出かけていた間に使う電気」で割った値の中央値を r とする。
      p ≥ 60% かつ r ≥ +5% なら A、p ≤ 40% かつ r ≤ −5% なら B、それ以外は C（勝ち負けが半々か、差がごく小さい）。

乱数の種は見本（並んだ2部屋）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
照合（check_answers）は run_checks を参照。
"""
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "aircon-tsukeppanashi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

N_TRIP = 10000
AWAY_MAIN = 30.0                                  # 本編の外出（分）
AWAY_RANGE = (10.0, 360.0)                        # ひねりの外出（分）
AFTER_H = 3.0                                     # 帰ってから何時間まで1刻みずつ計算するか（その先は tail で積分）
DT = 20.0                                         # 時間の刻み（秒）
SUBSTEPS = 40                                     # 温め直しの最中は、1歩をさらに40に分ける
YEN_PER_KWH = 31.0                                # 電気代の目安（1kWhあたり）

# ---------- 答えの規則（計算の前に決めた） ----------
P_HI, P_LO = 0.60, 0.40
R_MIN = 0.05


def answer_by_rule(p, r_med):
    """p = つけっぱなしのほうが少ない回の割合、r_med = 差 ÷ つけっぱなしの外出中の電気 の中央値"""
    if p >= P_HI and r_med >= R_MIN:
        return 0                                  # A つけっぱなし
    if p <= P_LO and r_med <= -R_MIN:
        return 1                                  # B こまめに消す
    return 2                                      # C ほぼ同じ


# ---------- エアコンの式（建築研究所 第四章 第三節 Ver.03） ----------
P_A = np.array([[-0.000056, 0.000786, 0.071625], [-0.000145, 0.003337, -0.143643], [-0.000240, -0.029471, 1.954343],
                [-0.000035, -0.050909, 1.389751], [0.0, 0.0, 0.076800]])
P_B = np.array([[0.000108, -0.035658, 3.063873], [-0.000017, 0.062546, -5.471556], [-0.000245, -0.025126, 4.057590],
                [0.000323, -0.021166, 0.575459], [0.0, 0.000330, 0.047500]])
P_C = np.array([[-0.001465, -0.030500, 1.920431], [0.002824, 0.041081, -1.835302], [-0.001929, -0.009738, 1.582898],
                [0.000616, -0.014239, 0.546204], [0.0, -0.000110, 0.023100]])
E_CLASS = ((-0.553e-3, 6.34), (-0.504e-3, 5.88), (-0.473e-3, 5.50))   # 定格冷房の効率の区分（い）（ろ）（は）
C_AF = 0.8                                        # 室内機の吹き出し風量に関する補正
C_DF = 0.77                                       # 霜取り（外 5℃未満かつ湿度 80%以上）


def p_coef(qrtd_c):
    """容量可変型の係数 p (5, 3)。定格冷房能力で表 A・B・C の間を直線で補間（式 9a〜9d）"""
    q = np.asarray(qrtd_c, float)[..., None, None]
    pa = P_A * (4000 - q) / 1800 + P_B * (q - 2200) / 1800
    pb = P_B * (7100 - q) / 3100 + P_C * (q - 4000) / 3100
    return np.where(q <= 2200, P_A, np.where(q <= 4000, pa, np.where(q < 7100, pb, P_C)))


def f_poly(p, th, x):
    """基準入出力関数 f_H,θ(x)（式 6・7）。p (n,5,3)、th (n,)、x (n,)"""
    a = p @ np.stack([th * th, th, np.ones_like(th)], -1)[..., None]
    a = a[..., 0]
    return (((a[..., 0] * x + a[..., 1]) * x + a[..., 2]) * x + a[..., 3]) * x + a[..., 4]


def make_ac(area, eclass, theta, rh):
    """広さ（m²）から機器の仕様（付録A）。返り値は1回ごとの配列の辞書"""
    qrtd_c = np.minimum(5600.0, 190.5 * area + 45.6)
    qrtd_h = 1.2090 * qrtd_c - 85.1
    qmax_c = np.maximum(qrtd_c, 0.8462 * qrtd_c + 1205.9)
    qmax_h = np.maximum(qrtd_h, 1.7597 * qmax_c - 413.7)
    qr = qmax_h / qrtd_h
    s, i = np.array(E_CLASS)[eclass].T
    ertd_h = 0.77 * (s * qrtd_c + i) + 1.66
    qq = np.minimum(qrtd_c, 5600.0) * 1e-3
    b = np.outer(qq, [0.000181, 0.002322, 0.003556]) + [-0.000184, 0.013904, 0.993431]
    c = np.outer(qq, [-0.000173, -0.003980, -0.002870]) + [0.000367, 0.003983, 0.006376]
    a = b * qr[:, None] + c
    d7 = theta - 7.0
    qrmax_out = a[:, 0] * d7 ** 2 + a[:, 1] * d7 + a[:, 2]          # 最大暖房出力比（式 2）
    cdf = np.where((theta < 5.0) & (rh >= 80.0), C_DF, 1.0)
    p = p_coef(qrtd_c)
    norm = f_poly(p, np.full_like(theta, 7.0), 1.0 / qr)
    return dict(qrtd_c=qrtd_c, qrtd_h=qrtd_h, qmax_h=qmax_h, qr=qr, ertd_h=ertd_h, p=p, norm=norm,
                theta=theta, cdf=cdf, Qmax=qrmax_out * qrtd_h * C_AF * cdf)


def ac_power(ac, Q):
    """部屋に入れる熱 Q（W）→ 消費電力（W）（式 5・10）。Q=0 なら 0"""
    x = Q / (C_AF * ac["cdf"]) / ac["qmax_h"]
    P = f_poly(ac["p"], ac["theta"], x) / ac["norm"] * ac["qrtd_h"] / ac["ertd_h"]
    return np.where(Q > 0, P, 0.0)


# ---------- 部屋 ----------

def make_rooms(n, rng):
    area = rng.uniform(10.0, 23.0, n)
    theta = rng.uniform(-2.0, 12.0, n)
    rh = rng.uniform(50.0, 95.0, n)
    tset = rng.uniform(20.0, 24.0, n)
    q = rng.uniform(1.6, 5.0, n)                  # 熱の逃げやすさ（W/m²K、床面積あたり）
    f_air = rng.uniform(0.35, 0.65, n)            # そのうち空気から直接逃げる割合（窓・すきま風・換気）
    cm = rng.uniform(110e3, 260e3, n)             # かたまりの熱容量（J/K、床面積あたり）
    furn = rng.uniform(5e3, 20e3, n)              # すぐ温まる家具など（J/K、床面積あたり）
    eclass = rng.integers(0, 3, n)
    return dict(area=area, theta=theta, rh=rh, tset=tset, q=q, f_air=f_air, cm=cm, furn=furn, eclass=eclass)


def physics(r):
    """部屋の値から、熱の通り道（W/K）と熱容量（J/K）"""
    A = r["area"]
    H = r["q"] * A
    Ha = r["f_air"] * H
    f_ms = 2.5 + 0.5 * np.clip((r["cm"] - 165e3) / 95e3, 0, 1)   # 重いつくりほど、つながる面積が大きい（2.5〜3）
    H_is = 3.45 * 4.5 * A
    H_ms = 9.1 * f_ms * A
    Ham = 1 / (1 / H_is + 1 / H_ms)
    Hrest = H - Ha                                # かたまりを通って逃げる分（直列: Ham と Hem）
    Hem = 1 / (1 / Hrest - 1 / Ham)
    Ca = 1.2 * 1006 * 2.5 * A + r["furn"] * A
    Cm = r["cm"] * A
    To, Ts = r["theta"], r["tset"]
    Tm_ss = (Ham * Ts + Hem * To) / (Ham + Hem)   # 落ち着いた時のかたまりの温度
    Q_ss = Ha * (Ts - To) + Ham * (Ts - Tm_ss)    # 設定温度を保つのに要る熱（W）
    ac = make_ac(A, r["eclass"], To, r["rh"])
    P_ss = ac_power(ac, Q_ss)
    return dict(H=H, Ha=Ha, Ham=Ham, Hem=Hem, Ca=Ca, Cm=Cm, To=To, Ts=Ts, Tm_ss=Tm_ss, Q_ss=Q_ss, ac=ac,
                P_ss=P_ss, cop_ss=Q_ss / P_ss)


def _sysmat(ph):
    """2つの温度（外との差）x = [空気, かたまり] の式 dx/dt = A x + b Q の A（1回ごと）"""
    a11 = -(ph["Ha"] + ph["Ham"]) / ph["Ca"]
    a12 = ph["Ham"] / ph["Ca"]
    a21 = ph["Ham"] / ph["Cm"]
    a22 = -(ph["Ham"] + ph["Hem"]) / ph["Cm"]
    return a11, a12, a21, a22


def _prop(A, Ca, h):
    """熱 Q を h 秒のあいだ一定にしたときの厳密な1歩: x' = Φ x + Γ Q（2×2 の行列の指数関数を閉じた式で）"""
    a11, a12, a21, a22 = A
    half = (a11 + a22) / 2
    disc = np.sqrt(((a11 - a22) / 2) ** 2 + a12 * a21)
    l1, l2 = half + disc, half - disc
    e1, e2 = np.exp(l1 * h), np.exp(l2 * h)
    c1 = (e1 - e2) / (l1 - l2)
    c0 = (l1 * e2 - l2 * e1) / (l1 - l2)
    F11, F12, F21, F22 = c0 + c1 * a11, c1 * a12, c1 * a21, c0 + c1 * a22
    det = a11 * a22 - a12 * a21
    G1 = (a22 * (F11 - 1) - a12 * F21) / (det * Ca)
    G2 = (-a21 * (F11 - 1) + a11 * F21) / (det * Ca)
    return F11, F12, F21, F22, G1, G2


def komame(ph, away_min, record=False, dt=DT, after_h=AFTER_H):
    """こまめに消す部屋: 出かけてから帰って after_h 時間後まで。away_min は1回ごとの配列か数。
    1歩ごとに熱 Q を一定とみなし、温度は厳密に進める（行列の指数関数）。温め方: 1歩の終わりに空気がちょうど
    設定温度になる Q を出す。ただし 0〜最大の熱 の範囲に切る。帰る時刻が1歩の途中なら、その歩を切った分とつけた分に分ける。
    返り値: 使った電気（Wh）、出した熱（J）、終わった時点の温度、ほか"""
    n = len(ph["To"])
    away = np.broadcast_to(np.asarray(away_min, float) * 60, (n,))
    t_end = away + after_h * 3600
    To, Ts = ph["To"], ph["Ts"]
    x1 = Ts - To                                  # 空気（外との差）
    x2 = ph["Tm_ss"] - To                         # かたまり（外との差）
    E = np.zeros(n)
    Qsum = np.zeros(n)
    Qmax = ph["ac"]["Qmax"]
    A = _sysmat(ph)
    hist = [] if record else None
    t = 0.0
    T_stop = float(t_end.max())
    t_back = np.full(n, np.nan)                  # 帰ってから設定温度に戻った時刻
    while t < T_stop - 1e-9:
        h_all = np.clip(t_end - t, 0.0, dt)
        h_off = np.clip(away - t, 0.0, h_all)
        h_on = h_all - h_off
        Fo = _prop(A, ph["Ca"], h_off)
        y1 = Fo[0] * x1 + Fo[1] * x2              # 切っている分
        y2 = Fo[2] * x1 + Fo[3] * x2
        on = h_on > 0
        # つけている分。まだ設定温度に届いていない部屋（全力から保つ運転に切りかわる歩を含む）は、1歩を細かく分ける
        # （電気は熱に対して下に凸なので、切りかわる歩を1つの Q で平均すると電気を少なく見積もる）
        rec = on & (y1 < Ts - To - 0.01)
        Qbar = np.zeros(n)
        Pacc = np.zeros(n)
        for sub, nsub in ((~rec & on, 1), (rec, SUBSTEPS)):
            idx = np.nonzero(sub)[0]
            if not len(idx):
                continue
            hh = h_on[idx] / nsub
            Ai = tuple(v[idx] for v in A)
            F11, F12, F21, F22, G1, G2 = _prop(Ai, ph["Ca"][idx], hh)
            a1, a2 = y1[idx], y2[idx]
            tgt = (Ts - To)[idx]
            acc = {k: ph["ac"][k][idx] if isinstance(ph["ac"][k], np.ndarray) and ph["ac"][k].shape[:1] == (n,)
                   else ph["ac"][k] for k in ph["ac"]}
            qs = np.zeros(len(idx))
            ps = np.zeros(len(idx))
            for _ in range(nsub):
                free1 = F11 * a1 + F12 * a2
                Q = np.clip((tgt - free1) / G1, 0.0, Qmax[idx])
                a1, a2 = free1 + G1 * Q, F21 * a1 + F22 * a2 + G2 * Q
                qs += Q * hh
                ps += ac_power(acc, Q) * hh
            y1[idx], y2[idx] = a1, a2
            Qbar[idx] = qs / np.maximum(h_on[idx], 1e-12)
            Pacc[idx] = ps
        x1, x2 = y1, y2
        Q, P = Qbar, Pacc / np.maximum(h_on, 1e-12)
        E += Pacc / 3600
        Qsum += Qbar * h_on
        hit = on & np.isnan(t_back) & (x1 >= Ts - To - 0.05)
        t_back[hit] = t + dt - away[hit]
        if record:
            hist.append(np.stack([x1 + To, x2 + To, Q, P]))
        t += dt
    out = dict(E=E, Qsum=Qsum, t_back=t_back, t_end=t_end, away=away, Ta=x1 + To, Tm=x2 + To)
    if record:
        out["hist"] = np.array(hist)              # (刻み, 4, n): 空気・かたまり・熱・電気
    return out


_GL_X, _GL_W = np.polynomial.legendre.leggauss(32)


def tail(ph, Ta, Tm):
    """くらべ終わった時点の、こまめに消す部屋の「残りの温め直し」に要る電気（Wh）。
    空気は設定温度に戻っていて（戻らない回は無い。run_checks で確かめる）、壁などのかたまりだけがまだ δ0 だけ冷たい。
    そのあとは空気を設定温度に保ったまま、かたまりの不足が時定数 τ = Cm / (Ham + Hem) で消えていき、
    その間エアコンはふだんより Ham·δ(t) だけ多く熱を出す。電気の増えた分を t = 0〜∞ で積分する（u = e^(−t/τ) と置いて、ガウス求積）。
    空気に残った不足（ごくわずか）は、ふだんの効率で足す"""
    d0 = np.maximum(0.0, ph["Tm_ss"] - Tm)
    tau = ph["Cm"] / (ph["Ham"] + ph["Hem"])
    u = (_GL_X + 1) / 2
    acc = np.zeros_like(d0)
    for uk, wk in zip(u, _GL_W / 2):
        acc += wk * (ac_power(ph["ac"], ph["Q_ss"] + ph["Ham"] * d0 * uk) - ph["P_ss"]) / uk
    air = ph["Ca"] * np.maximum(0.0, ph["Ts"] - Ta) / ph["cop_ss"]
    return (tau * acc + air) / 3600


def compare(ph, away_min, **kw):
    """つけっぱなし（ずっと P_ss）と、こまめに消す の差。ΔE > 0 なら つけっぱなしのほうが少ない。
    くらべるのは「出かけていた分のために使った電気」: つけっぱなしは留守中の電気、こまめに消すは
    帰ってから、ふだん（P_ss）より多く使った電気の合計（温め直し。残りの温め直しまで含む）。
    どちらも、それ以外の時間はふだんどおり P_ss を使うので、差 ΔE は「全部の電気」の差と同じ"""
    k = komame(ph, away_min, **kw)
    away = k["away"]
    res = tail(ph, k["Ta"], k["Tm"])
    np.seterr(divide="ignore", invalid="ignore")   # 外出0分の照合で 0 で割る（r は使わない）
    E_t_away = ph["P_ss"] * away / 3600
    E_k_extra = k["E"] - ph["P_ss"] * (k["t_end"] - away) / 3600 + res
    dE = E_k_extra - E_t_away
    # 温め直しで出した熱（ふだんより多く出した分。残りの分は Ham·δ0·τ ＋ 空気の不足）
    d0 = np.maximum(0.0, ph["Tm_ss"] - k["Tm"])
    tau = ph["Cm"] / (ph["Ham"] + ph["Hem"])
    heat_x = (k["Qsum"] - ph["Q_ss"] * (k["t_end"] - away) + ph["Ham"] * d0 * tau
              + ph["Ca"] * np.maximum(0.0, ph["Ts"] - k["Ta"]))
    return dict(E_t_away=E_t_away, E_k_extra=E_k_extra, dE=dE, r=dE / E_t_away, k=k, resid=res,
                heat_ratio=heat_x / np.maximum(1e-9, ph["Q_ss"] * away), cop_back=heat_x / np.maximum(1e-9, E_k_extra * 3600))


# ---------- 計算 ----------
SEED_MAIN, SEED_TW = 20261018, 20261019
GRID_MIN = np.array([10, 20, 30, 45, 60, 90, 120, 180, 240, 300, 360], float)
BINS = ((10, 30), (30, 60), (60, 120), (120, 240), (240, 360))   # ひねりの棒（外出の長さ・分）


def compute():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rooms = make_rooms(N_TRIP, np.random.default_rng(SEED_MAIN))
    ph = physics(rooms)
    m = compare(ph, AWAY_MAIN)
    print(f"本編 {time.time() - t0:.0f}秒")
    # 部屋ごとの境目: 同じ1万部屋で外出の長さを変える
    grid = []
    for g in GRID_MIN:
        grid.append(compare(ph, g)["dE"])
        print(f"  外出 {g:.0f}分 {time.time() - t0:.0f}秒")
    grid = np.array(grid)
    # ひねり: 外出の長さもでたらめにした別の1万回
    rng = np.random.default_rng(SEED_TW)
    rooms2 = make_rooms(N_TRIP, rng)
    away2 = np.exp(rng.uniform(math.log(AWAY_RANGE[0]), math.log(AWAY_RANGE[1]), N_TRIP))
    ph2 = physics(rooms2)
    w = compare(ph2, away2)
    np.savez_compressed(OUT / "data.npz", **{f"r_{k}": v for k, v in rooms.items()},
                        **{f"s_{k}": v for k, v in rooms2.items()}, away2=away2,
                        m_dE=m["dE"], m_r=m["r"], m_Ekx=m["E_k_extra"], m_Eta=m["E_t_away"], m_res=m["resid"],
                        m_back=m["k"]["t_back"], grid=grid, m_hr=m["heat_ratio"], m_copb=m["cop_back"],
                        w_dE=w["dE"], w_r=w["r"], w_res=w["resid"],
                        cop_ss=ph["cop_ss"], P_ss=ph["P_ss"], Q_ss=ph["Q_ss"], Qmax=ph["ac"]["Qmax"])
    print(f"計算 {time.time() - t0:.0f}秒")


_DATA = None


def data():
    global _DATA
    if _DATA is None:
        f = OUT / "data.npz"
        if not f.exists():
            raise SystemExit(f"{f} がありません。先に python sims/{SLUG}.py --compute を実行してください")
        z = np.load(f)
        _DATA = {k: z[k] for k in z.files}
    return _DATA


def rooms_of(prefix):
    d = data()
    keys = ("area", "theta", "rh", "tset", "q", "f_air", "cm", "furn", "eclass")
    return {k: d[f"{prefix}_{k}"] for k in keys}


def break_even(grid):
    """部屋ごとに、ΔE が 0 を下回る外出の長さ（分）。10分で既に下なら 0、6時間でも上なら inf"""
    n = grid.shape[1]
    out = np.full(n, np.inf)
    pos = grid > 0
    out[~pos[0]] = 0.0
    for j in range(1, len(GRID_MIN)):
        hit = np.isinf(out) & pos[j - 1] & ~pos[j]
        g0, g1 = grid[j - 1, hit], grid[j, hit]
        # 外出の長さは対数で補間する
        u = g0 / (g0 - g1)
        out[hit] = np.exp(np.log(GRID_MIN[j - 1]) + u * (np.log(GRID_MIN[j]) - np.log(GRID_MIN[j - 1])))
    return out


_SHOWN = None


def shown():
    global _SHOWN
    if _SHOWN is not None:
        return _SHOWN
    d = data()
    dE, r = d["m_dE"], d["m_r"]
    be = break_even(d["grid"])
    w_dE, away2 = d["w_dE"], d["away2"]
    bins = []
    for lo, hi in BINS:
        sel = (away2 >= lo) & (away2 < hi) if hi < 360 else (away2 >= lo)
        bins.append((lo, hi, int(sel.sum()), float(np.mean(w_dE[sel] > 0))))
    # 半々になる外出の長さ: 同じ1万部屋で長さを変えたときの「つけっぱなしのほうが少ない割合」が 50% を切る所（対数で補間）
    gp = np.array([np.mean(g > 0) for g in d["grid"]])
    half_min = float("nan")
    for j in range(1, len(GRID_MIN)):
        if gp[j - 1] >= 0.5 > gp[j]:
            u = (gp[j - 1] - 0.5) / (gp[j - 1] - gp[j])
            half_min = float(np.exp(np.log(GRID_MIN[j - 1]) + u * (np.log(GRID_MIN[j]) - np.log(GRID_MIN[j - 1]))))
            break
    # 外の気温・断熱で分けた境目（部屋ごと）
    rm = rooms_of("r")
    cold = rm["theta"] < 3
    warm = rm["theta"] >= 8
    leaky = rm["q"] >= 3.9
    tight = rm["q"] < 2.7
    _SHOWN = dict(
        p=float(np.mean(dE > 0)), r_med=float(np.median(r)), dE_med=float(np.median(dE)), dE_mean=float(np.mean(dE)),
        Eta_med=float(np.median(d["m_Eta"])), Ekx_med=float(np.median(d["m_Ekx"])),
        res_med=float(np.median(d["m_res"])), res_max_share=float(np.max(np.abs(d["m_res"]) / np.maximum(1e-9, np.abs(dE)))),
        back_med=float(np.nanmedian(d["m_back"])) / 60, cop_ss_med=float(np.median(d["cop_ss"])),
        cop_back_med=float(np.median(d["m_copb"])), heat_ratio_med=float(np.median(d["m_hr"])),
        be=be, be_med=float(np.median(be)), be_q=(float(np.quantile(be, 0.25)), float(np.quantile(be, 0.75))),
        be_lt30=float(np.mean(be < 30)), be_gt360=float(np.mean(np.isinf(be))),
        be_cold=float(np.median(be[cold])), be_warm=float(np.median(be[warm])),
        be_leaky=float(np.median(be[leaky])), be_tight=float(np.median(be[tight])),
        bins=bins, half_min=half_min, w_p=float(np.mean(w_dE > 0)),
        grid_p=[float(np.mean(g > 0)) for g in d["grid"]],
        dE=dE, r=r)
    return _SHOWN


def hm(mins):
    if not np.isfinite(mins):
        return "6時間超"
    h, m = divmod(int(round(mins)), 60)
    return f"{h}時間{m:02d}分" if h else f"{m}分"


def report():
    sh = shown()
    print(f"[外出30分] つけっぱなしのほうが少ない {sh['p']:.3f}  差の中央値 {sh['dE_med']:.1f}Wh（平均 {sh['dE_mean']:.1f}）"
          f"  差÷外出中の電気 中央値 {sh['r_med']:.3f}  つけっぱなしの外出中の電気 中央値 {sh['Eta_med']:.1f}Wh")
    print(f"   答え（規則）: {'ABC'[answer_by_rule(sh['p'], sh['r_med'])]}   温め直しの残りの補正 中央値 {sh['res_med']:.2f}Wh"
          f"  設定温度に戻るまで 中央値 {sh['back_med']:.1f}分  ふだんの効率 中央値 {sh['cop_ss_med']:.2f}"
          f"  温め直しの効率 中央値 {sh['cop_back_med']:.2f}  要る熱 ÷ 留守中の熱 中央値 {sh['heat_ratio_med']:.3f}")
    print(f"[境目・部屋ごと] 中央値 {hm(sh['be_med'])}  四分位 {hm(sh['be_q'][0])}〜{hm(sh['be_q'][1])}"
          f"  30分未満 {sh['be_lt30']:.3f}  6時間超 {sh['be_gt360']:.3f}")
    print(f"   外 3℃未満 {hm(sh['be_cold'])} / 8℃以上 {hm(sh['be_warm'])}   すきま多い(q≥3.9) {hm(sh['be_leaky'])} / 断熱よい(q<2.7) {hm(sh['be_tight'])}")
    print("   外出の長さ別 つけっぱなしが少ない割合:", {int(g): round(p, 3) for g, p in zip(GRID_MIN, sh["grid_p"])})
    print(f"[外出もでたらめな1万回] つけっぱなしが少ない {sh['w_p']:.3f}  半々になる長さ {hm(sh['half_min'])}")
    for lo, hi, n, p in sh["bins"]:
        print(f"   {lo}〜{hi}分: {n}回  つけっぱなしが少ない {p:.3f}")


if __name__ == "__main__" and "--compute" in sys.argv:
    compute()
    report()
    sys.exit(0)
if __name__ == "__main__" and "--report" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んだ2部屋）を選ぶ
# =====================================================================
SEED_PICK = 20261020
SAMPLE_AFTER_H = 12.0                             # 見本は帰って12時間後まで1刻みずつ（残りの温め直しが見えるように）


def pick_sample():
    """見本: 1万回とは別に引いた部屋から、ふつうの条件（外 4〜8℃・広さ 12〜18m²・設定 21〜23℃・断熱 中くらい）で、
    差 ΔE が1万回の中央値に近く、差 ÷ 留守中の電気も中央値に近いもの"""
    sh = shown()
    rr = make_rooms(40000, np.random.default_rng(SEED_PICK))
    ok = ((rr["theta"] >= 4) & (rr["theta"] <= 8) & (rr["area"] >= 12) & (rr["area"] <= 18) & (rr["tset"] >= 21)
          & (rr["tset"] <= 23) & (rr["q"] >= 2.5) & (rr["q"] <= 3.8) & (rr["rh"] < 80))
    idx = np.nonzero(ok)[0]
    sub = {k: v[idx] for k, v in rr.items()}
    c = compare(physics(sub), AWAY_MAIN)
    score = np.abs(c["dE"] - sh["dE_med"]) / sh["dE_med"] + np.abs(c["r"] - sh["r_med"]) / sh["r_med"]
    j = int(np.argmin(score))
    return {k: v[idx[j]:idx[j] + 1] for k, v in rr.items()}


_SAMPLE = {}


def sample():
    if not _SAMPLE:
        cache = OUT / "sample.npz"
        if cache.exists() and cache.stat().st_mtime > (OUT / "data.npz").stat().st_mtime:
            z = np.load(cache)
            room = {k: z[k] for k in z.files}
        else:
            room = pick_sample()
            np.savez(cache, **room)
        ph = physics(room)
        k = komame(ph, AWAY_MAIN, record=True, after_h=SAMPLE_AFTER_H)
        c = compare(ph, AWAY_MAIN)
        h = k["hist"][:, :, 0]
        ts = (np.arange(len(h)) + 1) * DT
        P = h[:, 3]
        away = AWAY_MAIN * 60
        extra = np.cumsum(np.where(ts > away, (P - float(ph["P_ss"][0])) * DT / 3600, 0.0))
        res = float(tail(ph, k["Ta"], k["Tm"])[0])
        _SAMPLE.update(room=room, ph=ph, ts=np.concatenate([[0.0], ts]), Ta=np.concatenate([[float(ph["Ts"][0])], h[:, 0]]),
                       Q=np.concatenate([[float(ph["Q_ss"][0])], h[:, 2]]), P=np.concatenate([[0.0], P]),
                       extra=np.concatenate([[0.0], extra]), res=res, P_ss=float(ph["P_ss"][0]),
                       Q_ss=float(ph["Q_ss"][0]), Qmax=float(ph["ac"]["Qmax"][0]), Ts=float(ph["Ts"][0]),
                       E_t_away=float(c["E_t_away"][0]), E_k_extra=float(c["E_k_extra"][0]), dE=float(c["dE"][0]),
                       t_back=float(k["t_back"][0]))
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    r = s["room"]
    print({k: np.round(v[0], 2) for k, v in r.items()})
    print(f"留守中 {s['E_t_away']:.1f}Wh  温め直し {s['E_k_extra']:.1f}Wh（うち12時間より後 {s['res']:.2f}）  差 {s['dE']:.1f}"
          f"  ふだん {s['P_ss']:.0f}W / 熱 {s['Q_ss']:.0f}W  最大の熱 {s['Qmax']:.0f}W  いちばん冷えた {s['Ta'].min():.1f}℃"
          f"  戻るまで {s['t_back'] / 60:.1f}分  いちばん大きい電気 {s['P'].max():.0f}W")
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, pct, stills  # noqa: E402

note.use()
note.DATE = "10.18"                               # 日付欄

COL_T, INK_T = "#ef8a3c", "#b4561a"               # つけっぱなし
COL_K, INK_K = "#5b8fd6", "#2f63a8"               # こまめに消す
SKY, SKY2 = "#2b3a5f", "#34466f"
WARM_IN, COLD_IN = "#ffe2bf", "#d3e3f4"           # 部屋の中の色（設定温度 / 6℃下）
WALL = "#f3ede0"
SNOW = "#ffffff"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_LEAVE = 0.55                                    # 本編の始めに2人が出かける（動画の秒、T_GO から）
RACE_AWAY = 3.6                                   # 留守の30分（動画の秒）
RACE_BACK = 3.0                                   # 帰ってから15分
BACK_MIN = 15.0
RACE_FF = 2.0                                     # その先、12時間後まで早送り
RACE_HOLD = 2.2
BIG_Q = ["30分の外出、エアコン暖房は", "つけっぱなしと消す、どっちが安い？"]
DETAIL = "冬の夜、同じ部屋2つでくらべる・1万回"
LABELS = ["つけっぱなし", "こまめに消す", "ほぼ同じ"]
CORRECT = 0                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める

# 冒頭と本編での家の絵の置き場所: (縮める倍率, 絵の上端の y)
LAY_INTRO = (1.0, 668.0)
LAY_SIM = (0.76, 588.0)
CX = 580.0


def setup():
    global T_RUN, T_BACK, T_FF, T_FF_END, T_RACE_END, T_G0, T_G1, T_BAR, T_REV, T_TW, T_TW_BAR, T_TW_BE, T_Q, DURATION
    T_RUN = T_GO + T_LEAVE                        # ここで時計が 0:00 から進む
    T_BACK = T_RUN + RACE_AWAY
    T_FF = T_BACK + RACE_BACK
    T_FF_END = T_FF + RACE_FF
    T_RACE_END = T_FF_END + RACE_HOLD
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.6
    T_BAR = T_G1 + 0.6                            # 棒（1万回の真ん中の値）
    T_REV = T_BAR + 1.2                           # 答え
    T_TW = T_REV + 3.6                            # ひねり
    T_TW_BAR = T_TW + 2.0
    T_TW_BE = T_TW_BAR + 2.0
    T_Q = T_TW_BE + 2.8                           # 締め
    DURATION = T_Q + 5.0


def sim_s(t):
    """動画の秒 → 見本の時計（出かけてからの秒）"""
    away = AWAY_MAIN * 60
    if t < T_RUN:
        return 0.0
    if t < T_BACK:
        return away * (t - T_RUN) / RACE_AWAY
    if t < T_FF:
        return away + BACK_MIN * 60 * (t - T_BACK) / RACE_BACK
    end = away + SAMPLE_AFTER_H * 3600
    a = away + BACK_MIN * 60
    u = clamp01((t - T_FF) / RACE_FF)
    return a + (end - a) * (u ** 2.2)              # 早送り（だんだん速く）


def at(arr, s):
    sm = sample()
    return float(np.interp(s, sm["ts"], arr))


def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_SIM[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_SIM[1] - LAY_INTRO[1]) * m)


def to_dev(lay, x, y):
    sc, y0 = lay
    return CX + (x - CX) * sc, y0 + y * sc


def apply_layout(ctx, lay):
    sc, y0 = lay
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)


# ---------- 家の絵（絵の座標: x は画面と同じ、y は絵の上端から） ----------
SKY_X0, SKY_X1, SKY_Y1 = 100.0, 1072.0, 782.0
ROOF_Y, APEX_Y = 168.0, 46.0
WALL_X0, WALL_X1, WALL_Y1 = 150.0, 1010.0, 688.0
ROOM_DX = 425.0                                   # 右の部屋は左の部屋をそのままずらしたもの（同じ部屋）
RX0, RX1 = 168.0, 568.0                           # 左の部屋の中
RY0, RY1 = 186.0, 676.0
WIN = (198.0, 238.0, 330.0, 372.0)                # 窓（x0, y0, x1, y1）
DOOR = (250.0, 470.0, 334.0, 676.0)
AC = (390.0, 200.0, 550.0, 246.0)
THERMO = (500.0, 300.0, 500.0, 460.0)


def _jit(seed, n, amp=1.2):
    return np.random.default_rng(seed).normal(0, amp, n)


def pen_rect(ctx, x0, y0, x1, y1, seed, width=3.0, color=INK, alpha=1.0):
    j = _jit(seed, 8)
    ctx.set_source_rgba(*hexrgb(color, alpha))
    ctx.set_line_width(width)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(x0 + j[0], y0 + j[1])
    ctx.line_to(x1 + j[2], y0 + j[3])
    ctx.line_to(x1 + j[4], y1 + j[5])
    ctx.line_to(x0 + j[6], y1 + j[7])
    ctx.close_path()
    ctx.stroke()


_FLAKES = None


def flakes():
    global _FLAKES
    if _FLAKES is None:
        rng = np.random.default_rng(9)
        n = 680
        _FLAKES = dict(x=rng.uniform(SKY_X0 - 40, SKY_X1 + 40, n), y=rng.uniform(0, SKY_Y1, n),
                       v=rng.uniform(80, 170, n), r=rng.uniform(3.0, 7.5, n), ph=rng.uniform(0, 2 * math.pi, n),
                       sw=rng.uniform(12, 30, n))
    return _FLAKES


def draw_snow(ctx, t):
    f = flakes()
    y = (f["y"] + f["v"] * t) % (SKY_Y1 + 20) - 10
    x = f["x"] + f["sw"] * np.sin(f["ph"] + t * 1.3)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    for xi, yi, ri in zip(x, y, f["r"]):
        ctx.new_sub_path()
        ctx.arc(xi, yi, ri, 0, 2 * math.pi)
    ctx.fill()


_SKY = None


def sky_surface():
    """夜空（紺の水彩っぽいむら）と月。毎コマ描かず、1枚作って貼る"""
    global _SKY
    if _SKY is None:
        w, h = int(SKY_X1 - SKY_X0) + 8, int(SKY_Y1) + 8
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        c = cairo.Context(s)
        c.translate(-SKY_X0 + 4, 4)
        fill(c, SKY)
        c.rectangle(SKY_X0, 0, SKY_X1 - SKY_X0, SKY_Y1)
        c.fill()
        rng = np.random.default_rng(4)
        c.save()
        c.rectangle(SKY_X0, 0, SKY_X1 - SKY_X0, SKY_Y1)
        c.clip()
        for _ in range(60):                       # むら
            c.set_source_rgba(*hexrgb(SKY2, rng.uniform(0.25, 0.6)))
            c.arc(rng.uniform(SKY_X0, SKY_X1), rng.uniform(0, SKY_Y1), rng.uniform(30, 110), 0, 2 * math.pi)
            c.fill()
        c.restore()
        fill(c, "#f7e7a6")                        # 月
        c.arc(985, 62, 30, 0, 2 * math.pi)
        c.fill()
        fill(c, SKY)
        c.arc(998, 54, 26, 0, 2 * math.pi)
        c.fill()
        pen_rect(c, SKY_X0, 0, SKY_X1, SKY_Y1, 1, width=3.5)
        _SKY = s
    return _SKY


def temp_color(dT):
    """設定温度より dT ℃ 下 → 部屋の中の色"""
    u = clamp01(dT / 6.0)
    a, b = hexrgb(WARM_IN), hexrgb(COLD_IN)
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3)) + (1.0,)


def house_static(ctx):
    """屋根・地面の雪"""
    fill(ctx, SNOW)
    ctx.move_to(SKY_X0, WALL_Y1 - 6)
    for k in range(13):
        x = SKY_X0 + (SKY_X1 - SKY_X0) * k / 12
        ctx.line_to(x, WALL_Y1 - 6 + 5 * math.sin(k * 1.7))
    ctx.line_to(SKY_X1, SKY_Y1)
    ctx.line_to(SKY_X0, SKY_Y1)
    ctx.close_path()
    ctx.fill()
    note.pen_line(ctx, SKY_X0 + 4, WALL_Y1 - 4, SKY_X1 - 4, WALL_Y1 - 2, INK, seed=12, width=3)
    rng = np.random.default_rng(13)                # 雪の起伏（うすい水色の線）
    ctx.set_source_rgba(*hexrgb("#9fbbd9", 0.8))
    ctx.set_line_width(2.5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k in range(9):
        cx = SKY_X0 + 60 + k * (SKY_X1 - SKY_X0 - 120) / 8 + rng.uniform(-25, 25)
        cy = WALL_Y1 + rng.uniform(30, 80)
        r = rng.uniform(40, 70)
        ctx.arc(cx, cy + r * 0.8, r, math.pi * 1.25, math.pi * 1.75)
        ctx.new_sub_path()
    ctx.stroke()
    fill(ctx, "#c9705a")                          # 屋根
    ctx.move_to(WALL_X0 - 30, ROOF_Y)
    ctx.line_to(CX, APEX_Y)
    ctx.line_to(WALL_X1 + 30, ROOF_Y)
    ctx.close_path()
    ctx.fill()
    fill(ctx, SNOW)                               # 屋根の雪
    ctx.move_to(WALL_X0 - 26, ROOF_Y - 4)
    ctx.line_to(CX, APEX_Y - 4)
    ctx.line_to(WALL_X1 + 26, ROOF_Y - 4)
    ctx.line_to(WALL_X1 + 10, ROOF_Y - 14)
    ctx.line_to(CX, APEX_Y + 10)
    ctx.line_to(WALL_X0 - 10, ROOF_Y - 14)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(3.5)
    ctx.move_to(WALL_X0 - 30, ROOF_Y)
    ctx.line_to(CX, APEX_Y)
    ctx.line_to(WALL_X1 + 30, ROOF_Y)
    ctx.close_path()
    ctx.stroke()


def draw_rooms(ctx, t, dT_k, on_k, q_t, q_k, people):
    """2つの部屋。dT_k = こまめに消す部屋が設定温度より何℃下か、q_* = 出している熱 ÷ 最大の熱、people = 人の位置"""
    ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
    fill(ctx, WALL)                               # 外壁（窓は穴）
    ctx.rectangle(WALL_X0, ROOF_Y, WALL_X1 - WALL_X0, WALL_Y1 - ROOF_Y)
    for dx in (0.0, ROOM_DX):
        x0, y0, x1, y1 = WIN
        ctx.rectangle(x0 + dx, y0, x1 - x0, y1 - y0)
    ctx.fill()
    for dx, dT in ((0.0, 0.0), (ROOM_DX, dT_k)):
        fill(ctx, temp_color(dT))
        ctx.rectangle(RX0 + dx, RY0, RX1 - RX0, RY1 - RY0)
        x0, y0, x1, y1 = WIN
        ctx.rectangle(x0 + dx, y0, x1 - x0, y1 - y0)
        ctx.fill()
    ctx.set_fill_rule(cairo.FILL_RULE_WINDING)
    pen_rect(ctx, WALL_X0, ROOF_Y, WALL_X1, WALL_Y1, 2, width=3.5)
    for k, dx in enumerate((0.0, ROOM_DX)):
        pen_rect(ctx, RX0 + dx, RY0, RX1 + dx, RY1, 20 + k, width=2.5, alpha=0.8)
        x0, y0, x1, y1 = WIN
        pen_rect(ctx, x0 + dx, y0, x1 + dx, y1, 30 + k, width=3)
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(2.5)
        ctx.move_to((x0 + x1) / 2 + dx, y0)
        ctx.line_to((x0 + x1) / 2 + dx, y1)
        ctx.move_to(x0 + dx, (y0 + y1) / 2)
        ctx.line_to(x1 + dx, (y0 + y1) / 2)
        ctx.stroke()
        d0, e0, d1, e1 = DOOR                     # ドア
        fill(ctx, "#c99a6b")
        ctx.rectangle(d0 + dx, e0, d1 - d0, e1 - e0)
        ctx.fill()
        pen_rect(ctx, d0 + dx, e0, d1 + dx, e1, 40 + k, width=3)
        fill(ctx, INK)
        ctx.arc(d1 + dx - 14, (e0 + e1) / 2 + 10, 5, 0, 2 * math.pi)
        ctx.fill()
        fill(ctx, hexrgb("#e9c9a0", 0.9))         # 床の敷物
        core.rrect(ctx, 360 + dx, 640, 180, 26, 10)
        ctx.fill()
        tx, ty0, _, ty1 = THERMO                  # 温度計（絵）
        dTk = 0.0 if k == 0 else dT_k
        ctx.set_source_rgba(1, 1, 1, 0.95)
        core.rrect(ctx, tx - 11 + dx, ty0, 22, ty1 - ty0, 11)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(2.5)
        ctx.stroke()
        lev = ty1 - 18 - (ty1 - ty0 - 40) * clamp01(0.75 - dTk / 8.0)
        fill(ctx, RED)
        ctx.rectangle(tx - 5 + dx, lev, 10, ty1 - 14 - lev)
        ctx.fill()
        ctx.arc(tx + dx, ty1 - 10, 14, 0, 2 * math.pi)
        ctx.fill()
        draw_ac(ctx, dx, (q_t if k == 0 else q_k), (True if k == 0 else on_k), t, seed=k)
    for (x, walking, a) in people:
        draw_person(ctx, x, RY1 - 2, walking, t, a)


def draw_ac(ctx, dx, q, on, t, seed=0):
    x0, y0, x1, y1 = AC
    fill(ctx, "#fbfbf8")
    core.rrect(ctx, x0 + dx, y0, x1 - x0, y1 - y0, 10)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_line_width(2)
    ctx.move_to(x0 + 14 + dx, y1 - 10)
    ctx.line_to(x1 - 14 + dx, y1 - 10)
    ctx.stroke()
    fill(ctx, "#47c27a" if on else "#b9b4a8")         # ランプ
    ctx.arc(x1 - 20 + dx, y0 + 14, 5, 0, 2 * math.pi)
    ctx.fill()
    if not on or q <= 0:
        return
    k = 0.25 + 0.75 * clamp01(q)                  # 温かい風（出している熱が大きいほど、長く・太く）
    n = 3 + int(round(4 * clamp01(q)))
    for i in range(n):
        u = (i + 0.5) / n
        bx = x0 + dx + 18 + (x1 - x0 - 36) * u
        L = 60 + 260 * k
        ph = (t * 2.2 + i * 0.37 + seed * 0.2) % 1.0
        ctx.set_source_rgba(*hexrgb(COL_T, 0.35 + 0.5 * k))
        ctx.set_line_width(3 + 3 * k)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        steps = 16
        for j in range(steps + 1):
            v = j / steps
            yy = y1 + 12 + L * v
            xx = bx - 70 * v * k + 9 * math.sin(2 * math.pi * (v * 1.6 - ph) + i)
            (ctx.move_to if j == 0 else ctx.line_to)(xx, yy)
        ctx.stroke()


def draw_person(ctx, x, yf, walking, t, a=1.0):
    """線画の人（マフラーつき）。yf は床"""
    if a <= 0:
        return
    sw = math.sin(t * 8) * (0.55 if walking else 0.0)
    ctx.save()
    ctx.translate(x, yf)
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(5)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    hip = (0, -62)
    for s0 in (0.16, -0.16):
        ang = s0 + (sw if s0 > 0 else -sw)
        ctx.move_to(*hip)
        ctx.line_to(62 * math.sin(ang), -62 + 62 * math.cos(ang))
    ctx.stroke()
    fill(ctx, hexrgb("#7a8fb8", a))               # 上着
    core.rrect(ctx, -17, -124, 34, 60, 10)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3)
    ctx.stroke()
    ctx.set_line_width(5)                         # 腕
    for s0 in (0.6, -0.6):
        ang = s0 - (sw if s0 > 0 else -sw) * 0.6
        ctx.move_to(s0 * 22, -114)
        ctx.line_to(s0 * 22 + 50 * math.sin(ang), -114 + 50 * math.cos(ang))
    ctx.stroke()
    fill(ctx, hexrgb("#ffffff", a))
    ctx.arc(0, -146, 19, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, a))
    ctx.set_line_width(3)
    ctx.stroke()
    fill(ctx, hexrgb(RED, a))                     # マフラー
    core.rrect(ctx, -18, -128, 36, 10, 4)
    ctx.fill()
    ctx.rectangle(6, -126, 9, 26)
    ctx.fill()
    ctx.restore()


_STATIC = {}


def static_surface(lay):
    key = (round(lay[0], 4), round(lay[1], 2))
    if key not in _STATIC:
        if len(_STATIC) > 4:
            _STATIC.clear()
        s = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        c = cairo.Context(s)
        apply_layout(c, lay)
        c.set_source_surface(sky_surface(), SKY_X0 - 4, -4)
        c.paint()
        _STATIC[key] = s
    return _STATIC[key]


def _pace(t):
    u = (t / 3.2) % 2.0
    return 360 + 140 * (u if u < 1 else 2 - u)


def people_at(t):
    """2人の位置: 冒頭は部屋の中を行ったり来たり。本編の始めにドアから出て、帰ったら入ってくる"""
    out = []
    door_x = (DOOR[0] + DOOR[2]) / 2
    for dx in (0.0, ROOM_DX):
        if t < T_GO:
            out.append((_pace(t) + dx, True, 1.0))
        elif t < T_RUN:
            x0 = _pace(T_GO)
            u = ease(clamp01((t - T_GO) / T_LEAVE))
            out.append((x0 + (door_x - x0) * u + dx, True, 1 - ease(clamp01((t - T_RUN + 0.15) / 0.15))))
        elif T_BACK <= t < T_BACK + 1.2:
            u = ease(clamp01((t - T_BACK) / 1.0))
            out.append((door_x + (385 - door_x) * u + dx, u < 1, ease(clamp01((t - T_BACK) / 0.15))))
        elif T_BACK + 1.2 <= t < T_G0:
            out.append((385 + dx, False, 1.0))
    return out


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    lay = layout(t)
    sm = sample()
    s = sim_s(t)
    ctx.push_group()
    ctx.set_source_surface(static_surface(lay), 0, 0)
    ctx.paint()
    ctx.save()
    apply_layout(ctx, lay)
    ctx.save()
    ctx.rectangle(SKY_X0, 0, SKY_X1 - SKY_X0, SKY_Y1)
    ctx.clip()
    draw_snow(ctx, t)
    house_static(ctx)
    ctx.restore()
    away = AWAY_MAIN * 60
    if t < T_RUN:
        dT_k, on_k = 0.0, True
        q_k = sm["Q_ss"] / sm["Qmax"]
    else:
        dT_k = sm["Ts"] - at(sm["Ta"], s)
        on_k = s >= away
        q_k = at(sm["Q"], s) / sm["Qmax"] if on_k else 0.0
    q_t = sm["Q_ss"] / sm["Qmax"]
    draw_rooms(ctx, t, dT_k, on_k, q_t, q_k, people_at(t))
    ctx.restore()
    for dx, lab, ink in ((0.0, "つけっぱなし", INK_T), (ROOM_DX, "こまめに消す", INK_K)):   # 部屋の名前（屋根の上）
        x, y = to_dev(lay, 368 + dx, 128)
        sz = 36 * lay[0] ** 0.5
        wl = core.text_width(lab, sz)
        fill(ctx, (*hexrgb(PAPER)[:3], 0.92))
        core.rrect(ctx, x - wl / 2 - 14, y - sz * 0.72, wl + 28, sz * 1.44, 10)
        ctx.fill()
        text(ctx, lab, x, y, sz, ink)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り（本編）: 時計・部屋の温度・いまの電気・使った電気の棒 ----------

def readout_alpha(t):
    if t < T_RUN - 0.3:
        return 0.0
    return ease_out((t - T_RUN + 0.3) / 0.35) * (1 - ease((t - T_G0) / 0.35))


def clock_str(s):
    m = int(s // 60)
    return f"{m // 60}:{m % 60:02d}"


def meter_vals(s):
    sm = sample()
    away = AWAY_MAIN * 60
    e_t = sm["P_ss"] * min(s, away) / 3600
    e_k = at(sm["extra"], s)
    if s >= sm["ts"][-1] - 1:
        e_k += sm["res"]
    return e_t, e_k


MB_X0, MB_LEN = 250.0, 560.0


def draw_meters(ctx, t, a, s):
    sm = sample()
    e_t, e_k = meter_vals(s)
    full = max(sm["E_t_away"], sm["E_k_extra"]) * 1.12
    rows = ((1258.0, "つけっぱなし … 留守のあいだの電気", e_t, COL_T, INK_T),
            (1383.0, "こまめに消す … 温め直しの電気", e_k, COL_K, INK_K))
    for y, lab, v, col, ink in rows:
        text(ctx, lab, MB_X0, y - 44, 30, ink, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(MB_X0, y - 18, MB_LEN, 36)
        ctx.stroke()
        w = MB_LEN * v / full
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, MB_X0, y - 18, w, 36, 5)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, f"{v:.0f}Wh", MB_X0 - 14, y, 32, ink, align="right", alpha=a)


def tag(ctx, s, x, y, size, color, a):
    """紙の札に字を書く（夜空や風の上でも読めるように）"""
    if a <= 0:
        return
    w = core.text_width(s, size)
    fill(ctx, (*hexrgb(PAPER)[:3], 0.93 * a))
    core.rrect(ctx, x - w / 2 - 12, y - size * 0.68, w + 24, size * 1.36, 8)
    ctx.fill()
    text(ctx, s, x, y, size, color, alpha=a)


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    sm = sample()
    lay = layout(t)
    s = sim_s(t)
    away = AWAY_MAIN * 60
    x, y = to_dev(lay, 330, 26)                   # 時計（夜空の左上。紙の札に書く）
    tag(ctx, f"出かけて {clock_str(s)}", x, y, 32, INK, a)
    x2, y2 = to_dev(lay, 830, 26)
    if T_FF <= t < T_FF_END:
        tag(ctx, "早送り ▶▶", x2, y2, 30, RED, a * ease_out((t - T_FF) / 0.3))
    else:
        tag(ctx, "留守のあいだ" if s < away else "帰宅後", x2, y2, 30, INK, a)
    for dx, key in ((0.0, "t"), (ROOM_DX, "k")):  # 部屋の温度・いまの電気
        if key == "t":
            Ta, P = sm["Ts"], sm["P_ss"]
        else:
            Ta = at(sm["Ta"], s)
            P = at(sm["P"], s) if s >= away else 0.0
        xa, ya = to_dev(lay, THERMO[0] + dx - 6, THERMO[3] + 46)
        tag(ctx, f"{Ta:.1f}℃", xa, ya, 30, INK_K if Ta < sm["Ts"] - 1 else INK, a)
        xp, yp = to_dev(lay, (AC[0] + AC[2]) / 2 + dx, AC[3] + 30)
        tag(ctx, f"{P:,.0f}W", xp, yp, 28, RED if P > sm["P_ss"] * 2 else INK, a)
    draw_meters(ctx, t, a, s)
    if T_RUN - 0.3 <= t < T_RUN + 1.6:            # 出かける・帰宅・早送り・差
        b = ease_out((t - T_RUN + 0.3) / 0.25) * (1 - ease((t - T_RUN - 1.3) / 0.3))
        note.sticky(ctx, "いってきます（右の部屋は OFF）", 580, 1138, 32, "yellow", a=b * a, tilt=-0.02)
    if T_BACK <= t < T_BACK + 2.2:
        b = ease_out((t - T_BACK) / 0.25) * (1 - ease((t - T_BACK - 1.9) / 0.3))
        note.sticky(ctx, "30分で帰宅 → スイッチ ON", 580, 1138, 34, "yellow", a=b * a, tilt=0.02)
    if T_FF <= t < T_FF_END + 0.2:
        b = ease_out((t - T_FF) / 0.25) * (1 - ease((t - T_FF_END) / 0.2))
        note.sticky(ctx, "冷えた壁や床も 温め直す", 580, 1138, 34, "blue", a=b * a, tilt=-0.02)
    if t >= T_FF_END:
        b = ease_out((t - T_FF_END) / 0.3) * a
        d = sm["E_k_extra"] - sm["E_t_away"]
        note.sticky(ctx, f"温め直しのほうが {abs(d):.0f}Wh {'多い' if d > 0 else '少ない'}", 580, 1138, 38, "pink",
                    fg=RED, a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_N, G_CELL = 100, 6
G_X0, G_Y0 = 580 - G_N * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_N
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    win = shown()["dE"] > 0
    cols = np.zeros((G_N, G_N, 4), np.uint8)
    flat = cols.reshape(-1, 4)
    m = min(N_TRIP, key * G_N)
    flat[:m] = np.where(win[:m, None], np.array(bgra(COL_T), np.uint8), np.array(bgra(COL_K), np.uint8))
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_BAR) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    n = N_TRIP * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_N * G_CELL + 7, G_N * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000部屋（外出30分）", 580, 612, 34, INK, alpha=a)
    win = sh["dE"][:int(n)] > 0
    cnt = (int(win.sum()), int((~win).sum()))
    for i, (lab, col) in enumerate((("つけっぱなしが少ない", COL_T), ("こまめに消すが少ない", COL_K))):
        y = 1300 + i * 56
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(232, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 282, y, 36, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt[i])}回", 905, y, 36, INK, align="right", alpha=a)
    text(ctx, "1マス＝1部屋。外の気温・広さ・断熱は毎回でたらめ", 580, 1412, 26, PENCIL, bold=False, alpha=a)


# ---------- 棒: 出かけていた分の電気（1万回の真ん中の値・同じものさし） ----------
BX0, BLEN = 250.0, 560.0


def draw_hbar(ctx, y, frac, col, lab, val, a, g=1.0):
    text(ctx, lab, BX0, y - 46, 32, INK, align="left", alpha=a)
    w = BLEN * frac * g
    if w > 1:
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        core.rrect(ctx, BX0, y - 20, w, 40, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.stroke()
    tw = core.text_width(val, 36)
    vx = BX0 + w + 14
    if vx + tw > 925:
        vx = BX0 + w - tw - 12
    text(ctx, val, vx, y, 36, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def bars_alpha(t):
    if t < T_BAR:
        return 0.0
    return ease_out((t - T_BAR) / 0.3) * (1 - ease((t - T_TW) / 0.3))


def draw_bars(ctx, t):
    a = bars_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "出かけていた30分のために 使った電気", 580, 640, 38, INK, alpha=a)
    text(ctx, "（1万回の真ん中の値）", 580, 690, 30, PENCIL, bold=False, alpha=a)
    full = max(sh["Eta_med"], sh["Ekx_med"]) * 1.15
    g1 = ease_out((t - T_BAR - 0.1) / 0.4)
    g2 = ease_out((t - T_BAR - 0.4) / 0.4)
    draw_hbar(ctx, 810, sh["Eta_med"] / full, COL_T, "つけっぱなし（留守のあいだ）", f"{sh['Eta_med']:.0f}Wh", a, g1)
    draw_hbar(ctx, 945, sh["Ekx_med"] / full, COL_K, "こまめに消す（温め直し）", f"{sh['Ekx_med']:.0f}Wh", a, g2)
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.2) / 0.3) * a
        note.sticky(ctx, "30分なら つけっぱなしが少ない", 580, 1100, 40, "pink", fg=RED, a=b, tilt=-0.02)
        b2 = ease_out((t - T_REV - 0.8) / 0.3) * a
        text(ctx, f"1万部屋のうち {pct(sh['p'])}%（{fmt(round(sh['p'] * N_TRIP))}部屋）", 580, 1228, 34, INK, bold=False, alpha=b2)
        yen = sh["dE_med"] / 1000 * YEN_PER_KWH
        text(ctx, f"ただし差は 1回 約{yen:.1f}円（1円にも満たない）", 580, 1288, 34, INK, bold=False, alpha=b2)
        text(ctx, f"（電気代は 1kWh {YEN_PER_KWH:.0f}円で計算）", 580, 1340, 28, PENCIL, bold=False, alpha=b2)


# ---------- ひねり: 何時間までなら？ ----------
TW_Q = "じゃあ、何時間までなら\nつけっぱなしが得？"
TB_X0, TB_LEN = 330.0, 520.0


def bin_label(lo, hi):
    def f(m):
        return f"{m // 60}時間" if m >= 60 else f"{m}分"
    return f"{f(lo)}〜{f(hi)}"


def be_words(mins):
    """境目の長さを、画面用にざっくり（15分きざみ）"""
    q = int(round(mins / 15.0)) * 15
    h, m = divmod(q, 60)
    if h == 0:
        return f"{m}分"
    return f"{h}時間" if m == 0 else f"{h}時間{m}分"


def draw_twist(ctx, t):
    if t < T_TW or t >= T_Q + 0.4:
        return
    sh = shown()
    fade = 1 - ease((t - T_Q) / 0.35)
    if t < T_TW_BAR:
        ba = ease_out((t - T_TW) / 0.25)
        note.banner(ctx, TW_Q, 580, 860, a=ba, t_rel=t - T_TW, size=48)
        return
    a = ease_out((t - T_TW_BAR) / 0.3) * fade
    text(ctx, TW_Q, 580, 660, 44, INK, alpha=fade)
    text(ctx, "つけっぱなしのほうが少なかった部屋の割合", 580, 762, 30, PENCIL, bold=False, alpha=a)
    text(ctx, "（外出の長さも10分〜6時間でたらめにした1万回）", 580, 804, 26, PENCIL, bold=False, alpha=a)
    y0 = 880
    x50 = TB_X0 + TB_LEN * 0.5
    for i, (lo, hi, n, p) in enumerate(sh["bins"]):
        y = y0 + i * 92
        g = ease_out((t - T_TW_BAR - 0.15 - 0.18 * i) / 0.35)
        text(ctx, bin_label(lo, hi), TB_X0 - 16, y, 32, INK, align="right", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.3 * a))
        ctx.set_line_width(2)
        ctx.rectangle(TB_X0, y - 22, TB_LEN, 44)
        ctx.stroke()
        w = TB_LEN * p * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(COL_T, 0.95 * a))
            core.rrect(ctx, TB_X0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        val = f"{pct(p)}%"
        tw = core.text_width(val, 34)
        vx = TB_X0 + w + 12
        if vx + tw > 925:
            vx = TB_X0 + w - tw - 12
        text(ctx, val, vx, y, 34, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    ctx.set_source_rgba(*hexrgb(RED, 0.8 * a))    # 半分の線
    ctx.set_line_width(3)
    ctx.set_dash([9, 8])
    ctx.move_to(x50, y0 - 36)
    ctx.line_to(x50, y0 + 4 * 92 + 36)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "半分", x50, y0 + 4 * 92 + 60, 28, RED, alpha=a)
    if t >= T_TW_BE:
        b = ease_out((t - T_TW_BE) / 0.3) * a
        note.sticky(ctx, f"境目は だいたい {be_words(sh['half_min'])}", 580, 1385, 40, "yellow", a=b, tilt=-0.02)


# ---------- 冒頭・上のブロック ----------

def choice_row(labels, size, cx, max_w, gap=72):
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


CD_X, CD_Y = 580.0, 1400.0


class AIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、雪の夜の家と同じ部屋2つ（0秒目から雪・風・人が動く）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 60
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 800:
            sz *= 800 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (408, 478)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 516, 575 + w2 / 2 + 6, 511, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 560, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 860, gap=48)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 622, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 622, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 622, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:                     # 予想して！と 5・4・3・2・1・0（家の下の雪の上に）
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            note.hand_text(ctx, "予想して！", cx - 70, cy, 50, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx + 130, cy, 46, 44, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx + 130, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 70, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
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


INTRO = AIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------
END_Q = "なんで、消して温め直すほうが\n電気を食うの？"
END_A = "温め直しは、効率の悪い全力運転"


def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    draw_grid(ctx, t)
    draw_bars(ctx, t)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q > 0:
        sh = shown()
        note.sticky(ctx, END_Q, 580, 790, 48, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.3) / 0.3)
        note.sticky(ctx, END_A, 580, 1010, 46, "pink", fg=RED, a=r, tilt=0.02)
        r2 = ease_out((t - T_Q - 1.8) / 0.3)
        text(ctx, f"電気1で出せる熱: ふだん {sh['cop_ss_med']:.1f} → 温め直し {sh['cop_back_med']:.1f}", 580, 1140, 32, INK,
             bold=False, alpha=r2)
        text(ctx, f"（要る熱は {pct(1 - sh['heat_ratio_med'])}%少ないのに）", 580, 1192, 30, PENCIL, bold=False, alpha=r2)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def band_noise(dur, lo, hi, seed, rms):
    rng = np.random.default_rng(seed)
    n = int(SR * dur)
    X = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    band = np.clip((f - lo) / 60, 0, 1) * np.clip((hi - f) / 200, 0, 1)
    x = np.fft.irfft(X * band, n)
    x /= max(1e-9, float(np.sqrt(np.mean(x ** 2))))
    return x * rms


def build_audio():
    sm = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 293.7, 370.0)), 1.0, bgm=True)
    tt = np.arange(int(SR * DURATION)) / SR
    wind = band_noise(DURATION, 150.0, 900.0, 3, 0.02) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.13 * tt))   # 外の風
    mx.add(0, wind * np.where(tt < T_G0, 1.0, 0.4), 1.0, bgm=True)
    hum = band_noise(DURATION, 80.0, 400.0, 5, 0.03)   # エアコンの音（2部屋の電気に合わせる）
    away = AWAY_MAIN * 60
    env = np.zeros_like(tt)
    for i in range(0, len(tt), 480):
        t = tt[i]
        if t >= T_G0:
            break
        s = sim_s(t)
        Pk = sm["P_ss"] if t < T_RUN else (at(sm["P"], s) if s >= away else 0.0)
        env[i:i + 480] = 0.5 + 0.25 * (sm["P_ss"] + Pk) / sm["P_ss"]
    env = np.convolve(env, np.ones(2400) / 2400, mode="same")
    mx.add(0, hum * np.clip(env, 0, 3.0), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    mx.add(T_RUN - 0.2, blip(523.3, 0.12), 0.35)          # ドア
    mx.add(T_RUN, tick(1200, 0.05), 0.5)                  # スイッチ OFF
    mx.add(T_BACK, blip(880.0, 0.15), 0.5)                # スイッチ ON（ピッ）
    mx.add(T_BACK + 0.05, riser(0.8), 0.35)
    mx.add(T_FF, whoosh(0.8), 0.3)
    mx.add(T_FF_END, bell(784.0, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_BAR + 0.1, blip(587.3, 0.15), 0.35)
    mx.add(T_BAR + 0.4, blip(784.0, 0.15), 0.35)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_TW, riser(0.8), 0.45)                        # ひねり
    for i in range(5):
        mx.add(T_TW_BAR + 0.15 + 0.18 * i, blip(659.3 - 40 * i, 0.12), 0.3)
    mx.add(T_TW_BE, bell(1046.5, 1.2), 0.4)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.3, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    d = data()
    checks = []
    rr = make_rooms(500, np.random.default_rng(7))
    ph = physics(rr)
    # (1) エアコンの式: 外 7℃・定格の熱を出しているとき、消費電力は 定格能力 ÷ 定格の効率（式5の作り）
    ac7 = make_ac(rr["area"], rr["eclass"], np.full(500, 7.0), np.full(500, 60.0))
    P_rated = ac_power(ac7, ac7["qrtd_h"] * C_AF)
    checks.append(("外7℃・定格の熱で、消費電力 = 定格能力 ÷ 定格効率（最大のずれ W）",
                   float(np.max(np.abs(P_rated - ac7["qrtd_h"] / ac7["ertd_h"]))), 0.0, 1e-6))
    # (2) 全力のときの効率は、ふだん（設定温度を保つ）の効率より低い（全部の部屋で）
    cop_full = ph["ac"]["Qmax"] / ac_power(ph["ac"], ph["ac"]["Qmax"])
    checks.append(("全力の効率 < ふだんの効率（全部の部屋）", float(np.all(cop_full < ph["cop_ss"])), 1.0, 0.0))
    # (3) 外出0分なら差は0（設定温度を保つ計算と、つけっぱなしの式が一致）
    z = compare(ph, 0.0)
    checks.append(("外出0分の差（最大 Wh）", float(np.max(np.abs(z["dE"]))), 0.0, 0.05))
    # (4) 切っている間の冷え方が、2つの温度の連立方程式の厳密解（行列の指数関数）と一致（30分後の空気の温度）
    k = komame(ph, 30.0, record=True, after_h=0.0)
    Ta30 = k["hist"][int(1800 / DT) - 1, 0]
    err = []
    for i in range(0, 500, 25):
        A = np.array([[-(ph["Ha"][i] + ph["Ham"][i]) / ph["Ca"][i], ph["Ham"][i] / ph["Ca"][i]],
                      [ph["Ham"][i] / ph["Cm"][i], -(ph["Ham"][i] + ph["Hem"][i]) / ph["Cm"][i]]])
        lam, V = np.linalg.eig(A)
        x0 = np.array([ph["Ts"][i] - ph["To"][i], ph["Tm_ss"][i] - ph["To"][i]])
        x = V @ (np.exp(lam * 1800) * np.linalg.solve(V, x0))
        err.append(abs(Ta30[i] - (x[0] + ph["To"][i])))
    checks.append(("切って30分後の室温が厳密解と一致（最大のずれ ℃）", float(max(err)), 0.0, 0.03))
    # (5) 残りの温め直しの積分（tail）: 3時間で切って積分しても、12時間まで刻んでも同じ
    a3 = compare(ph, 30.0)
    a12 = compare(ph, 30.0, after_h=12.0)
    checks.append(("tail の積分と12時間の計算の差（最大 Wh）", float(np.max(np.abs(a3["dE"] - a12["dE"]))), 0.0, 0.05))
    # (6) 刻みを半分にしても差は変わらない
    h = compare(ph, 30.0, dt=DT / 2)
    checks.append(("刻み 20秒と10秒の差の中央値のずれ（Wh）", float(np.median(a3["dE"]) - np.median(h["dE"])), 0.0, 0.1))
    # (7) 帰ってから全部の部屋が設定温度に戻った
    checks.append(("本編: 全部の部屋が設定温度に戻った", float(np.isfinite(d["m_back"]).all()), 1.0, 0.0))
    # (8) 外出が長いほど、つけっぱなしが勝つ割合は下がる
    gp = np.array(sh["grid_p"])
    checks.append(("外出が長いほど つけっぱなしが勝つ割合が下がる", float(np.all(np.diff(gp) <= 1e-9)), 1.0, 0.0))
    # (9) 答え
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["p"], sh["r_med"])), float(INTRO.correct), 0.0))
    checks.append(("画面の境目（15分きざみ）が、部屋ごとの境目の中央値と同じ丸め",
                   float(be_words(sh["half_min"]) == be_words(sh["be_med"])), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    sm = sample()
    print(f"長さ {DURATION:.1f}秒  見本: 留守 {sm['E_t_away']:.0f}Wh / 温め直し {sm['E_k_extra']:.0f}Wh")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, T_GO + 0.3, T_RUN + 1.0, T_RUN + 3.0, T_BACK + 0.5, T_BACK + 1.5, T_BACK + 2.8,
              T_FF + 1.0, T_FF_END + 1.0, T_G0 + 1.5, T_G1 + 0.3, T_BAR + 1.0, T_REV + 1.5, T_TW + 1.0, T_TW_BAR + 1.5,
              T_TW_BE + 1.5, T_Q + 1.0, T_Q + 3.0, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
