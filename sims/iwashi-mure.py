"""サメに襲われたら、イワシの群れの真ん中は安全？ サメの「狩り」（何度もの突っ込み）を1万回。— 2026-10-29 作り直し（公開予定 11.11・ナレーションなし・45秒前後）

くらべるのは「1回の狩りで食べられたイワシのうち、狩りの始めに真ん中の4分の1にいたものの割合 p」。平等（どこにいても同じ）なら p = 25%。

【計算の前に固定した条件】（この下の数字は 1万回を回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  群れ   : 500匹。横から見た平面。1匹あたり 2 BL²（BL＝イワシの体長1つ分）。形は 丸・縦長・横長（縦横比 2:1）が 3分の1ずつ。向きは回ごとにでたらめ。
           中の並びは ずらした六角格子＋ゆらぎ（16通りの型）。「真ん中」＝中心に近い 125匹（群れの4分の1。楕円でも面積が 1/4 なので「半径の半分以内」と同じ）。
  1回の狩り : サメが 10〜40回（一様にでたらめ）突っ込む。突っ込みのたびに、食べられたイワシは群れから消える。
  群れの締まり直し : 突っ込みのあと、群れは まわりとの間隔（1匹あたりの面積）を保ったまま 真ん中へ寄って締まり直す
           （残った全員の中心からの距離を √(残り匹数/500) 倍する）。外側が薄くなっても 穴は そのまま残らず、真ん中に寄る。
  サメ   : 1回の狩りで 速さ（水に対して）Vs = 3×k BL/秒（k は 1.5〜5 から一様＝「群れの最高速 3 BL/秒 の 1.5〜5倍」）。
           群れは 0〜3 BL/秒（一様）で 全員 +x 向きに泳ぐ。サメは 群れの後ろ側の半分（向き ±90°）から追いつく向きに来る
           （Krause ほか 2017: 襲撃36回すべて 群れの後ろから。後ろ側だけにする）。群れに乗った目で見たサメの速さ Vrel は ベクトルの差で出す。
  突っ込み : 群れの中心のまわりの でたらめな1点（中心から ガウス分布・標準偏差 = 群れの半径×0.4）をねらって まっすぐ突っ込む（群れの中を通り抜ける突っ込みもある）。
           口の幅 W = 2 BL（出典なし・仮定。幅の半分 = 1.0 BL）。最初に口の範囲に入った1匹が 食べられる。口に入るイワシが 1匹もいなければ 空振り。
  逃げ   : イワシは サメが R_D（1〜3 BL から一様）まで近づくと気づき、突っ込みの線から離れる向きに 横へ逃げる（flash expansion を 単純にしたもの）。
           気づいてから動き出すまでの遅れは イワシごとに 0.03秒（半分）か 0.10秒（半分）（ニシンの音への反応の遅れが 約30 ms と約100 ms の2つの山: Domenici & Batty 1994。割合 50% は仮定）。
           横へ逃げる速さ 5 BL/秒（仮定）。サメが届くまでの時間 T = R_D / Vrel。横へ動く距離 D = 5×max(0, T − 遅れ)。
           突っ込みの線からの横のずれ |l| に D を足して 口の幅の半分（1.0 BL）より小さければ、その魚は口の範囲に残る。
           「サメは一番近い魚をねらう」は使わない（台本の変更）。
  ねらい  : 範囲に残った魚のうち、突っ込みの向きで いちばん先に当たる1匹が 食べられる。

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  1万回の狩りのうち「食べられた魚が 1匹以上いた狩り」で p を出し、その 中央値（1万回を並べた ちょうど真ん中の値）を p とする。
  p ≤ 15% → 真ん中のほうが安全 ／ p ≥ 35% → 端のほうが安全 ／ それ以外 → ほぼ同じ

【あわせて出す数字】
  ・真ん中の魚が 1匹でも食べられた狩りは 何回に1回か
  ・真ん中の1匹・端の1匹が 1回の狩りで食べられる確率（真ん中の1匹が生き残る割合）
  ・ひねり: 「では、狩りが長く続くと？」＝突っ込みの回数 10・20・30・40回別に、同じ1万回の狩りの途中経過で 上の数字を出す（全部の狩りを 40回まで回し、途中の累計を使う）

【絵について】計算は500匹のまま。絵は 魚が見えるよう大きく描くため、代表の約125匹（真ん中の4分の1から約31匹・そのほかから約94匹）に、
  その狩りで食べられる魚を足したものだけを描く（群れの形・突っ込み・逃げる動き・食べられる順は計算そのもの）。

問い: 「サメに襲われたら、/ イワシの群れの / 真ん中は安全？」
      選択肢: 真ん中のほうが安全 ／ ほぼ同じ ／ 端のほうが安全（正解の記号が B になるよう、計算のあとに並びを入れ替える）
見せ方: 見本の1回の狩り（1万回の中の1回そのもの）→ 食べられた魚の場所を1万回ぶん点で積む →「真ん中は p・1匹でも食べられた狩りは○回に1回」
ひねり: 「では、狩りが長く続くと？」
締め: 「あなたがイワシなら、群れのどこを泳ぎますか？」
言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。画面に「計算での見立て」を小さく1回。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "iwashi-mure"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_HUNT = 10000
SEED_MAIN = 20261111
N_FISH = 500
N_INNER = 125                                        # 真ん中＝中心に近い 4分の1
AREA = N_FISH * 2.0                                  # 群れの面積（BL²）
R_UNIT = math.sqrt(AREA / math.pi)                   # 丸の半径 ≒ 17.8 BL
ASPECT = 2.0                                         # 縦長・横長の縦横比
U_MAX = 3.0                                          # 群れの最高速（BL/秒）
K_MIN, K_MAX = 1.5, 5.0                              # サメの速さ = 3 × k
P_MIN, P_MAX = 10, 40                                # 1回の狩りの突っ込みの回数
SIGMA_AIM = 0.4                                      # ねらう点のずれ（群れの半径に対して）
RD_MIN, RD_MAX = 1.0, 3.0                            # イワシがサメに気づく距離（BL）
FB = 5.0                                             # 横へ逃げる速さ（BL/秒）
LAT_FAST, LAT_SLOW = 0.03, 0.10                      # 動き出すまでの遅れ（秒）
P_FAST = 0.5                                         # 遅れが短いイワシの割合
W_HALF = 1.0                                         # 口の幅の半分（BL）
N_TPL = 16
M_SHOW = (10, 20, 30, 40)                            # ひねり: 突っ込みの回数
P_CENTER, P_EDGE = 0.15, 0.35                        # 答えの決め方のしきい値
CFG0 = dict(fb=FB, w=W_HALF, pfast=P_FAST, sigma=SIGMA_AIM, lat=(LAT_FAST, LAT_SLOW), rd=(RD_MIN, RD_MAX))


def answer_by_rule(p):
    """p: 食べられた魚のうち 真ん中の4分の1 だった割合（狩りごと）の 中央値。戻り値は 'center'（真ん中のほうが安全）/'same'（ほぼ同じ）/'edge'（端のほうが安全）"""
    if p <= P_CENTER:
        return "center"
    if p >= P_EDGE:
        return "edge"
    return "same"


def shape_ab(shape):
    """0=丸 1=縦長 2=横長 の半径（ψ=0 のときの x, y 方向）"""
    if shape == 0:
        return R_UNIT, R_UNIT
    s = math.sqrt(ASPECT)
    return (R_UNIT * s, R_UNIT / s) if shape == 2 else (R_UNIT / s, R_UNIT * s)


def make_templates():
    """単位円の中に 500点。ずらした六角格子の、中心に近い500点にゆらぎを足し、いちばん外が半径1になるよう割る"""
    rng = np.random.default_rng(777)
    tpls = []
    for _ in range(N_TPL):
        s = 1.0
        ii, jj = np.meshgrid(np.arange(-30, 31), np.arange(-30, 31))
        x = s * (ii + 0.5 * jj)
        y = s * (math.sqrt(3) / 2) * jj
        off = rng.uniform(0, s, 2)
        pts = np.stack([x.ravel() + off[0], y.ravel() + off[1]], 1)
        pts = pts[np.argsort((pts ** 2).sum(1))[:N_FISH]]
        pts = pts + rng.normal(0, 0.2 * s, pts.shape)
        r = np.sqrt((pts ** 2).sum(1))
        pts = pts / r.max()
        tpls.append(pts)
    return np.array(tpls)


_TPL = {}


def templates():
    if "t" not in _TPL:
        _TPL["t"] = make_templates()
    return _TPL["t"]


def draw_params(rng):
    """1回の狩りの条件（狩りの中の突っ込みごとの乱数は run_hunt が続けて引く）"""
    shape = int(rng.integers(3))
    psi = float(rng.uniform(0, math.pi))
    u = float(rng.uniform(0, U_MAX))
    k = float(rng.uniform(K_MIN, K_MAX))
    tpl = int(rng.integers(N_TPL))
    rot = float(rng.uniform(0, 2 * math.pi))
    flip = int(rng.integers(2))
    n_pass = int(rng.integers(P_MIN, P_MAX + 1))
    return dict(shape=shape, psi=psi, U=u, k=k, tpl=tpl, rot=rot, flip=flip, n_pass=n_pass)


def school(par):
    """戻り値: P0（群れの上の位置 BL）, Tn（楕円にそった正規化位置 単位円）, inner（真ん中の4分の1か）"""
    T = templates()[par["tpl"]].copy()
    c, s = math.cos(par["rot"]), math.sin(par["rot"])
    T = np.stack([T[:, 0] * c - T[:, 1] * s, T[:, 0] * s + T[:, 1] * c], 1)
    if par["flip"]:
        T[:, 1] = -T[:, 1]
    a, b = shape_ab(par["shape"])
    X, Y = T[:, 0] * a, T[:, 1] * b
    c, s = math.cos(par["psi"]), math.sin(par["psi"])
    P0 = np.stack([X * c - Y * s, X * s + Y * c], 1)
    r = np.sqrt((T ** 2).sum(1))
    inner = np.zeros(N_FISH, bool)
    inner[np.argsort(r)[:N_INNER]] = True
    return P0, T, inner


def pass_core(pos, q, d, vrel, rd, lat, cfg):
    """1回の突っ込み。pos=いまの位置, q=ねらう点, d=突っ込みの向き（単位ベクトル）。戻り値 (食べられる魚の番号（pos の中）か -1, 横のずれ l, 前後の位置 s, 逃げる距離 D)"""
    nvec = np.array([-d[1], d[0]])
    rel = pos - q
    l = rel @ nvec
    s = rel @ d
    D = cfg["fb"] * np.maximum(0.0, rd / vrel - lat)
    cand = np.abs(l) + D < cfg["w"]
    if cand.any():
        cs = np.nonzero(cand)[0]
        return int(cs[np.argmin(s[cs])]), l, s, D
    return -1, l, s, D


def run_hunt(rng, cfg=CFG0, rec=False):
    """1回の狩り（40回の突っ込みまで回し、累計を残す。その狩りの突っ込みは n_pass 回）"""
    par = draw_params(rng)
    P0, Tn, inner = school(par)
    alive = np.ones(N_FISH, bool)
    cumE = np.zeros(P_MAX, np.int16)
    cumI = np.zeros(P_MAX, np.int16)
    ev = []
    Vs, U = 3.0 * par["k"], par["U"]
    e = i = 0
    recs = [] if rec else None
    for m in range(P_MAX):
        idx = np.nonzero(alive)[0]
        sc = math.sqrt(len(idx) / N_FISH)
        pos = P0[idx] * sc
        alpha = float(rng.uniform(-math.pi / 2, math.pi / 2))
        q = rng.normal(0.0, cfg["sigma"] * R_UNIT * sc, 2)
        rd = float(rng.uniform(*cfg["rd"]))
        lat = np.where(rng.random(len(idx)) < cfg["pfast"], cfg["lat"][0], cfg["lat"][1])
        v = np.array([Vs * math.cos(alpha) - U, Vs * math.sin(alpha)])
        vrel = math.hypot(v[0], v[1])
        d = v / vrel
        j, l, s, D = pass_core(pos, q, d, vrel, rd, lat, cfg)
        hit = -1
        if j >= 0:
            hit = int(idx[j])
            alive[hit] = False
            e += 1
            i += int(inner[hit])
            ev.append((m, hit))
        cumE[m], cumI[m] = e, i
        if rec:
            recs.append(dict(ids=idx, sc=sc, q=q, d=d, vrel=vrel, rd=rd, l=l, s=s, D=D, hit=hit, alpha=alpha))
    out = dict(par=par, cumE=cumE, cumI=cumI, ev=ev, Tn=Tn, inner=inner, P0=P0)
    if rec:
        out["recs"] = recs
    return out


def run_many(seed, n, cfg=CFG0):
    """n回の狩り。戻り値: 狩りごとの配列と、食べられた魚ごとの配列（ev_*）"""
    n_pass = np.zeros(n, np.int16)
    shape = np.zeros(n, np.int8)
    U = np.zeros(n)
    K = np.zeros(n)
    cumE = np.zeros((n, P_MAX), np.int16)
    cumI = np.zeros((n, P_MAX), np.int16)
    eh, em, ex, ey, ei, er = [], [], [], [], [], []
    for h in range(n):
        r = run_hunt(np.random.default_rng([seed, h]), cfg)
        par = r["par"]
        n_pass[h], shape[h], U[h], K[h] = par["n_pass"], par["shape"], par["U"], par["k"]
        cumE[h], cumI[h] = r["cumE"], r["cumI"]
        for m, j in r["ev"]:
            eh.append(h)
            em.append(m)
            ex.append(r["Tn"][j, 0])
            ey.append(r["Tn"][j, 1])
            ei.append(bool(r["inner"][j]))
            er.append(math.hypot(*r["Tn"][j]))
    return dict(n_pass=n_pass, shape=shape, U=U, k=K, cumE=cumE, cumI=cumI,
                ev_h=np.array(eh, np.int32), ev_m=np.array(em, np.int8), ev_tx=np.array(ex, np.float32),
                ev_ty=np.array(ey, np.float32), ev_inner=np.array(ei, bool), ev_rn=np.array(er, np.float32))


def hunt_stats(cumE, cumI, m):
    """m（狩りごとの突っ込みの回数。整数か配列）までの累計から 数字を出す"""
    H = len(cumE)
    mm = np.broadcast_to(np.asarray(m), (H,))
    E = cumE[np.arange(H), mm - 1].astype(int)
    I = cumI[np.arange(H), mm - 1].astype(int)
    has = E > 0
    p_med = float(np.median(I[has] / E[has])) if has.any() else 0.0
    return dict(E=E, I=I, p_med=p_med, p_pool=float(I.sum() / max(E.sum(), 1)), frac_c=float((I > 0).mean()),
                zero=int((~has).sum()), d_c=float(I.sum() / (N_INNER * H)), d_e=float((E - I).sum() / ((N_FISH - N_INNER) * H)),
                mean_E=float(E.mean()))


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万回の狩り。計算には1分ほどかかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"hunts_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        main = {k: z[k] for k in z.files}
    else:
        import time
        t0 = time.time()
        main = run_many(SEED_MAIN, N_HUNT)
        print(f"  1万回の狩り {time.time() - t0:.0f}秒")
        np.savez_compressed(f, **main)
    st = hunt_stats(main["cumE"], main["cumI"], main["n_pass"].astype(int))
    by_m = {m: hunt_stats(main["cumE"], main["cumI"], m) for m in M_SHOW}
    _RES["m"] = dict(main=main, st=st, p=st["p_med"], by_m=by_m)
    return _RES["m"]


SENS = (("基準", {}), ("逃げる速さ 3 BL/秒", dict(fb=3.0)), ("逃げる速さ 8 BL/秒", dict(fb=8.0)),
        ("口の幅 1 BL（半分0.5）", dict(w=0.5)), ("口の幅 3 BL（半分1.5）", dict(w=1.5)),
        ("遅れ 全員0.03秒", dict(pfast=1.0)), ("遅れ 全員0.10秒", dict(pfast=0.0)),
        ("ねらいのずれ 0.2", dict(sigma=0.2)), ("ねらいのずれ 0.7", dict(sigma=0.7)),
        ("気づく距離 0.5〜1.5 BL", dict(rd=(0.5, 1.5))), ("気づく距離 2〜4 BL", dict(rd=(2.0, 4.0))))


def sensitivity(n=1500):
    """置き方を変えたとき 答えが動くか（情報）"""
    rows = []
    for nm, kw in SENS:
        cfg = dict(CFG0)
        cfg.update(kw)
        m = run_many(SEED_MAIN + 7, n, cfg)
        st = hunt_stats(m["cumE"], m["cumI"], m["n_pass"].astype(int))
        rows.append((nm, st))
    return rows


def report():
    r = results()
    m, st = r["main"], r["st"]
    key = answer_by_rule(r["p"])
    print(f"乱数の種 {SEED_MAIN}  {N_HUNT}回の狩り  群れ{N_FISH}匹（真ん中{N_INNER}匹＝{N_INNER / N_FISH:.0%}）  突っ込み {P_MIN}〜{P_MAX}回")
    print(f"  p（食べられた魚があった狩りでの、真ん中の割合の中央値）= {r['p'] * 100:.2f}% → {key}   (平等なら 25%)")
    print(f"  全部まとめた割合 {st['p_pool'] * 100:.2f}%  食べられた魚が0匹の狩り {st['zero']}回  1回の狩りで食べられた数: 平均 {st['mean_E']:.1f} 匹 最大 {st['E'].max()}")
    nc = int((st["I"] > 0).sum())
    print(f"  真ん中の魚が1匹でも食べられた狩り: {nc}回 / {N_HUNT}（{st['frac_c'] * 100:.1f}%）" + (f" → 約{1 / st['frac_c']:.1f}回に1回" if nc else ""))
    print(f"  1匹あたり 食べられる確率: 真ん中 {st['d_c'] * 100:.3f}%  端 {st['d_e'] * 100:.3f}%  → 端は真ん中の {st['d_e'] / max(st['d_c'], 1e-12):.1f}倍  真ん中の1匹が生き残る {100 - st['d_c'] * 100:.2f}% / 端 {100 - st['d_e'] * 100:.2f}%")
    print(f"  食べられた魚の総数 {len(m['ev_h'])}匹（狩り40回まで）  うち真ん中 {int(m['ev_inner'].sum())}匹  いちばん内側 半径 {m['ev_rn'].min():.3f}")
    print("  突っ込みの回数別（同じ1万回の狩りの途中経過）:")
    for mm, s_ in r["by_m"].items():
        print(f"    {mm}回: p中央値 {s_['p_med'] * 100:.2f}%  全部まとめ {s_['p_pool'] * 100:.2f}%  真ん中が1匹でも食べられた狩り {s_['frac_c'] * 100:.1f}%  平均 {s_['mean_E']:.1f}匹  0匹の狩り {s_['zero']}")
    for s_i, nm in ((0, "丸"), (1, "縦長"), (2, "横長")):
        sel = m["shape"] == s_i
        t = hunt_stats(m["cumE"][sel], m["cumI"][sel], m["n_pass"][sel].astype(int))
        print(f"  形 {nm}: p中央値 {t['p_med'] * 100:.2f}%  真ん中が1匹でも食べられた狩り {t['frac_c'] * 100:.1f}%（{int(sel.sum())}回）")
    for lo, hi in ((0, 1), (1, 2), (2, 3.01)):
        sel = (m["U"] >= lo) & (m["U"] < hi)
        t = hunt_stats(m["cumE"][sel], m["cumI"][sel], m["n_pass"][sel].astype(int))
        print(f"  群れの速さ {lo}〜{min(hi, 3)}: p中央値 {t['p_med'] * 100:.2f}%  真ん中が1匹でも食べられた狩り {t['frac_c'] * 100:.1f}%  平均 {t['mean_E']:.1f}匹")


def report_sensitivity():
    print("感度（置き方を変える。各1500回・情報）:")
    for nm, st in sensitivity():
        print(f"  {nm}: p中央値 {st['p_med'] * 100:5.2f}%  全部まとめ {st['p_pool'] * 100:5.2f}%  真ん中が1匹でも食べられた狩り {st['frac_c'] * 100:5.1f}%  平均 {st['mean_E']:.1f}匹  0匹の狩り {st['zero']}  → {answer_by_rule(st['p_med'])}")


# ---- MODEL END ----


def report_extra():
    """MODEL の外（結果の保存に影響しない）"""
    r = results()
    m = r["main"]
    print(f"  サメの k の平均 {m['k'].mean():.2f}  群れの速さ U の平均 {m['U'].mean():.2f}  突っ込みの回数の平均 {m['n_pass'].mean():.1f}")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--timing" in sys.argv:
        import time
        t0 = time.time()
        run_many(SEED_MAIN, 200)
        print(f"200回の狩り {time.time() - t0:.1f}秒")
        sys.exit(0)
    report()
    report_extra()
    if "--nosens" not in sys.argv:
        report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す1回の狩り）を、1万回の中から選ぶ
# =====================================================================
N_SHOW = 10                                          # 見本の突っ込みの回数（動画の長さのため 10回の狩りから選ぶ）
_SAMPLE = {}


def samples():
    """丸い群れ・突っ込み10回・1回目の突っ込みで1匹食べられ・真ん中は食べられず・食べられた数が 同じ条件の狩りの中で真ん中に近い 1回の狩り。
    1万回の中の1回そのもの（同じ乱数で動きを記録し直す）"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    m, st = r["main"], r["st"]
    E, I = st["E"], st["I"]
    pool = (m["n_pass"] == N_SHOW) & (E > 0)
    tgt = float(np.median(E[pool]))
    ok = pool & (m["shape"] == 0) & (I == 0) & (m["cumE"][:, 0] == 1) & (E >= 4) & (E <= 9)
    ids = np.nonzero(ok)[0]
    h = int(ids[np.argmin(np.abs(E[ids] - tgt))])
    rec = run_hunt(np.random.default_rng([SEED_MAIN, h]), rec=True)
    recs = rec["recs"][:N_SHOW]
    inner = rec["inner"]
    eaten = [rc["hit"] for rc in recs if rc["hit"] >= 0]
    drawn = np.zeros(N_FISH, bool)                    # 絵に描く魚: 代表（真ん中から4匹に1匹・そのほかから4匹に1匹）＋ 食べられる魚
    drawn[np.nonzero(inner)[0][::4]] = True
    drawn[np.nonzero(~inner)[0][::4]] = True
    drawn[eaten] = True
    _SAMPLE.update(h=h, rec=rec, recs=recs, drawn=drawn, E=int(E[h]), tgt=tgt)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    S = samples()
    print(f"見本: 狩り #{S['h']}  突っ込み {N_SHOW}回  食べられた {S['E']}匹（同条件の中央 {S['tgt']:.0f}）  1回目に食べられた {S['recs'][0]['hit']}  描く魚 {int(S['drawn'].sum())}匹")
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
note.DATE = "11.11"                                  # 日付欄（公開予定日）

GOLD, GOLD_D = "#f7b61f", "#a56d00"                  # 真ん中の4分の1のイワシ（金の印）
SILV, SILV_D = "#dfe7ef", "#5d6f84"                  # そのほか（銀の印）
DOT_OUT = "#3f7fb5"
WATER_T, WATER_B = "#bfe6f2", "#4f93b8"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は B（2番目）
LABELS = ["ほぼ同じ", "真ん中のほうが安全", "端のほうが安全"]
KEY_LABEL = {"center": "真ん中のほうが安全", "same": "ほぼ同じ", "edge": "端のほうが安全"}
CORRECT = 1                                         # answer_by_rule の結果の位置（B）

BIG_Q3 = ["サメに襲われたら、", "イワシの群れの", "真ん中は安全？"]          # 1コマ目の3行（同じ大きさ）
BIG_Q = ["サメに襲われたら、", "イワシの群れの真ん中は安全？"]               # 定位置（上）の2行
DETAIL_RULE = "真ん中＝中心から半径の半分まで（群れの4分の1）"
DETAIL = "サメは群れへ突っ込み、口に当たった1匹を食べる、という計算での見立て"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 960.0, 870.0
CARD_X = 60.0
CARD_Y_INTRO, CARD_Y_FINAL = 840.0, 610.0
CD_X, CD_Y = 790.0, 970.0
SC = 21.0                                           # カード内の 1 BL = 21 px
SCX, SCY = 480.0, 470.0                             # カード内の、群れの中心
L_FISH = 40.0                                       # 絵のイワシの体長（px）。計算の1 BL（14px）より大きく描く
L_SHARK = 300.0
SH_PAD = 16.0                                       # サメは群れの外 16 BL から入り、16 BL 先へ抜ける
P_FIRST, P_REST = 1.6, 0.65                         # 1回目の突っ込み（ゆっくり）と 2回目以降の長さ（秒）

DOT_R = 260.0                                       # 点の図（正規化した群れ）の半径 px
DOT_C = (330.0, 950.0)
TW_X = (200.0, 420.0, 640.0, 860.0)                  # 棒グラフの中心 x
TW_BASE, TW_H = 1005.0, 290.0                       # 棒グラフの底の y と 100% の高さ


def setup():
    global T_SH0, T_HEND, T_D0, T_D1, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TS1, T_TW2, T_Q, DURATION, SCENES, PASS_T0, PASS_DUR
    T_SH0 = T_GO + 0.5                              # 1回目の突っ込みの始まり
    PASS_DUR = [P_FIRST] + [P_REST] * (N_SHOW - 1)
    PASS_T0 = [T_SH0 + sum(PASS_DUR[:k]) for k in range(N_SHOW)]
    T_HEND = T_SH0 + sum(PASS_DUR)                  # 10回の突っ込みが終わる
    T_D0 = T_HEND + 3.4                             # 点の図へ
    T_D1 = T_D0 + 0.8 + 3.6                         # 点が積み終わる
    T_DN = T_D1 + 0.1                               # 数字1（p）
    T_DN2 = T_DN + 2.8                              # 数字2（何回に1回）
    T_REV = T_DN2 + 3.0                             # 答え
    T_ANS2 = T_REV + 2.8                            # 理由
    T_TW = T_ANS2 + 3.4                             # ひねり
    T_TS1 = T_TW + 0.8 + 1.8                        # 棒が伸び終わる
    T_TW2 = T_TW + 4.2                              # ひねりの答え
    T_Q = T_TW2 + 3.6                               # 締め
    DURATION = T_Q + 4.8
    SCENES = [("見本の1回の狩り", T_GO, T_D0), ("食べられた魚の場所・1万回（答え・理由）", T_D0, T_TW),
              ("ひねり（突っ込みの回数別）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def p1(x):
    """割合 → 小数1桁の%（0.0556 → '5.6%'）"""
    return f"{math.floor(x * 1000 + 0.5) / 10:.1f}%"


def once_in(f):
    """割合 f（0〜1）→ 約N回に1回。1回に1回に近いときは 小数1桁"""
    v = 1.0 / f
    return f"約{v:.1f}回に1回" if v < 10 else f"約{int(round(v))}回に1回"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


# ---------- 絵: イワシ・サメ ----------

def fish_shape(ctx, L):
    """原点が体の中心、頭が +x。体長 L"""
    ctx.new_path()
    ctx.move_to(0.5 * L, 0)
    ctx.curve_to(0.30 * L, -0.23 * L, -0.25 * L, -0.19 * L, -0.40 * L, -0.04 * L)
    ctx.line_to(-0.40 * L, 0.04 * L)
    ctx.curve_to(-0.25 * L, 0.19 * L, 0.30 * L, 0.23 * L, 0.5 * L, 0)
    ctx.close_path()


def draw_fish(ctx, x, y, ang, L, gold, wag=0.0, a=1.0, glow=0.0):
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    if glow > 0:
        ctx.set_source_rgba(1.0, 0.97, 0.7, 0.8 * glow)
        ctx.arc(0, 0, L * 1.3, 0, 2 * math.pi)
        ctx.fill()
    ctx.save()                                          # 尾びれ
    ctx.translate(-0.38 * L, 0)
    ctx.rotate(wag)
    ctx.move_to(0, 0)
    ctx.line_to(-0.34 * L, -0.24 * L)
    ctx.line_to(-0.34 * L, 0.24 * L)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(GOLD_D if gold else SILV_D, 0.95 * a))
    ctx.fill()
    ctx.restore()
    fish_shape(ctx, L)
    ctx.set_source_rgba(*hexrgb(GOLD if gold else SILV, a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(GOLD_D if gold else SILV_D, 0.9 * a))
    ctx.set_line_width(max(0.9, L * 0.06))
    ctx.stroke()
    if L >= 9:
        ctx.arc(0.28 * L, -0.04 * L, max(0.9, L * 0.055), 0, 2 * math.pi)
        ctx.set_source_rgba(0.08, 0.1, 0.18, a)
        ctx.fill()
    ctx.restore()


def draw_shark(ctx, x, y, ang, L, a=1.0):
    """サメの影。頭が +x。丸い目の、こわくない絵柄"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    if abs(ang) > math.pi / 2:
        ctx.scale(1, -1)                               # 左向きのとき 背びれが下にならないよう 上下を返す
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.push_group()
    ctx.move_to(0.02 * L, -0.12 * L)                     # 背びれ・尾びれ・胸びれ
    ctx.line_to(-0.10 * L, -0.34 * L)
    ctx.line_to(-0.20 * L, -0.12 * L)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#33465c"))
    ctx.fill()
    ctx.move_to(-0.42 * L, 0.0)
    ctx.line_to(-0.62 * L, -0.26 * L)
    ctx.line_to(-0.55 * L, 0.0)
    ctx.line_to(-0.62 * L, 0.20 * L)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(0.12 * L, 0.10 * L)
    ctx.line_to(-0.02 * L, 0.30 * L)
    ctx.line_to(-0.10 * L, 0.10 * L)
    ctx.close_path()
    ctx.fill()
    ctx.move_to(0.5 * L, 0.03 * L)                       # 体
    ctx.curve_to(0.38 * L, -0.20 * L, -0.05 * L, -0.19 * L, -0.45 * L, -0.02 * L)
    ctx.line_to(-0.45 * L, 0.02 * L)
    ctx.curve_to(-0.05 * L, 0.20 * L, 0.38 * L, 0.18 * L, 0.5 * L, 0.03 * L)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#3d5069"))
    ctx.fill_preserve()
    _stroke(ctx, max(2.0, L * 0.02), "#1d2a3a", 0.9)
    ctx.move_to(0.46 * L, 0.05 * L)                      # おなか
    ctx.curve_to(0.30 * L, 0.17 * L, -0.05 * L, 0.18 * L, -0.40 * L, 0.02 * L)
    ctx.curve_to(-0.05 * L, 0.10 * L, 0.30 * L, 0.10 * L, 0.46 * L, 0.05 * L)
    ctx.set_source_rgba(*hexrgb("#c9d6e4", 0.9))
    ctx.fill()
    ctx.arc(0.33 * L, -0.045 * L, 0.040 * L, 0, 2 * math.pi)   # 目
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.fill()
    ctx.arc(0.34 * L, -0.045 * L, 0.020 * L, 0, 2 * math.pi)
    ctx.set_source_rgba(0.05, 0.07, 0.12, 1)
    ctx.fill()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: 水の中 ----------
_WATER = {}


def water_bg():
    if "s" in _WATER:
        return _WATER["s"]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(CARD_W), int(CARD_H))
    c = cairo.Context(s)
    g = cairo.LinearGradient(0, 0, 0, CARD_H)
    g.add_color_stop_rgb(0, *hexrgb(WATER_T)[:3])
    g.add_color_stop_rgb(1, *hexrgb(WATER_B)[:3])
    c.set_source(g)
    c.paint()
    c.move_to(0, CARD_H)                                # 海底（すこし）
    for i in range(0, 20):
        c.line_to(i * 52.0, CARD_H - 26 - 9 * math.sin(i * 1.7))
    c.line_to(CARD_W, CARD_H)
    c.close_path()
    c.set_source_rgba(*hexrgb("#b9a77a", 0.55))
    c.fill()
    for x0, w in ((120, 70), (330, 50), (560, 90), (760, 55)):      # 光の筋
        c.move_to(x0, 0)
        c.line_to(x0 + w, 0)
        c.line_to(x0 - 90 + w, CARD_H)
        c.line_to(x0 - 90, CARD_H)
        c.close_path()
        c.set_source_rgba(1, 1, 1, 0.10)
        c.fill()
    _WATER["s"] = s
    return s


_PART = {}


def draw_particles(ctx, t, u):
    """プランクトンの粒。群れに乗った目では、水が群れと反対に流れる（画面では右へ）。u=群れの速さ"""
    if "p" not in _PART:
        rng = np.random.default_rng(5)
        _PART["p"] = (rng.uniform(0, CARD_W, 70), rng.uniform(30, CARD_H - 30, 70), rng.uniform(0, 6.28, 70))
    xs, ys, ph = _PART["p"]
    for i in range(70):
        x = (xs[i] + (u * SC * 1.0 + 6.0) * t) % CARD_W
        y = ys[i] + 5 * math.sin(t * 0.8 + ph[i])
        ctx.arc(x, y, 1.6 + (i % 3) * 0.6, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.35)
        ctx.fill()
    for i in range(7):                                  # あわ
        x = 90 + i * 120 + 12 * math.sin(t * 1.3 + i)
        y = CARD_H - ((t * 40 + i * 97) % (CARD_H + 40))
        ctx.arc(x, y, 5 + (i % 3) * 2, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 0.45)
        ctx.set_line_width(2)
        ctx.stroke()


def to_card(p):
    """群れの上の位置（BL）→ カード内の px。画面では右から追ってくるように見せるため 左右を返す（群れは左へ泳ぐ）"""
    return SCX - p[..., 0] * SC, SCY + p[..., 1] * SC


def pass_geom(k):
    """k回目の突っ込みの、サメの通る道（σ の始めと終わり）と 食べられる魚が当たる時刻・位置"""
    S = samples()
    rc = S["recs"][k]
    sa, sb = float(rc["s"].min()) - SH_PAD, float(rc["s"].max()) + SH_PAD
    out = dict(sa=sa, sb=sb)
    if rc["hit"] >= 0:
        loc = int(np.nonzero(rc["ids"] == rc["hit"])[0][0])
        sh = float(rc["s"][loc])
        out["t_cross"] = PASS_T0[k] + PASS_DUR[k] * (sh - sa) / (sb - sa)
        nvec = np.array([-rc["d"][1], rc["d"][0]])
        sg = 1.0 if rc["l"][loc] >= 0 else -1.0
        pos = S["rec"]["P0"][rc["hit"]] * rc["sc"] + nvec * sg * float(rc["D"][loc])
        out["xy"] = tuple(float(v) for v in to_card(pos))
    return out


def hunt_state(t):
    """時刻 t の見本の狩り: 描く魚の (x, y, 向き, 金か, 食べられる途中か)、サメ、閃光、数え"""
    S = samples()
    recs, P0 = S["recs"], S["rec"]["P0"]
    inner = S["rec"]["inner"]
    if t < T_SH0:
        k, u = 0, 0.0
    else:
        k = max(i for i in range(N_SHOW) if PASS_T0[i] <= t)
        u = clamp01((t - PASS_T0[k]) / PASS_DUR[k])
    rc = recs[k]
    g = pass_geom(k)
    ids, s, l, D, d, sc, rd = rc["ids"], rc["s"], rc["l"], rc["D"], rc["d"], rc["sc"], rc["rd"]
    nvec = np.array([-d[1], d[0]])
    sigma = g["sa"] + (g["sb"] - g["sa"]) * u
    sel = np.nonzero(S["drawn"][ids])[0]
    gid = ids[sel]
    ds = s[sel] - sigma
    f = np.where(ds >= 0, smooth((rd - ds) / rd), smooth(1 + ds / rd))
    sg = np.where(l[sel] >= 0, 1.0, -1.0)
    disp = sg * D[sel] * f
    pos = P0[gid] * sc + nvec[None, :] * disp[:, None]
    fx, fy = to_card(pos)
    # 逃げる向き（突っ込みの線から離れる向き）へ 少し向きを変える
    nvx, nvy = -float(nvec[0]), float(nvec[1])
    tgt = np.arctan2(sg * nvy, sg * nvx)
    wgt = f * np.minimum(1.0, D[sel])
    dang = (tgt - math.pi + math.pi) % (2 * math.pi) - math.pi
    ang = math.pi + dang * 0.6 * wgt
    # 食べられる魚は 当たった後 消える
    gone = np.zeros(len(gid), bool)
    if rc["hit"] >= 0 and t >= g["t_cross"] + 0.1:
        gone = gid == rc["hit"]
    # 数え
    eaten = sum(1 for j in range(k) if recs[j]["hit"] >= 0)
    eaten_in = sum(1 for j in range(k) if recs[j]["hit"] >= 0 and inner[recs[j]["hit"]])
    if rc["hit"] >= 0 and t >= g["t_cross"]:
        eaten += 1
        eaten_in += int(inner[rc["hit"]])
    # 閃光（食べられた直後 0.5秒）
    flashes = []
    for j in range(k + 1):
        if recs[j]["hit"] >= 0:
            gj = pass_geom(j)
            if gj["t_cross"] <= t < gj["t_cross"] + 0.5:
                flashes.append((gj["xy"], t - gj["t_cross"]))
    # サメ
    shark = None
    if T_SH0 <= t <= T_HEND:
        px, py = (float(v) for v in to_card(rc["q"] + d * sigma))
        ramp = min(1.0, u / 0.10, (1 - u) / 0.10)
        shark = (px, py, math.atan2(float(d[1]), -float(d[0])), clamp01(ramp))
    return dict(fx=fx, fy=fy, ang=ang, gold=inner[gid], gone=gone, gid=gid, sc=sc, k=k, eaten=eaten, eaten_in=eaten_in,
                flashes=flashes, shark=shark)


def draw_water_card(ctx, t):
    """カードの中身（水・群れ・サメ）。t は動画の秒"""
    ctx.set_source_surface(water_bg(), 0, 0)
    ctx.paint()
    S = samples()
    draw_particles(ctx, t, S["rec"]["par"]["U"])
    st = hunt_state(t)
    ctx.arc(SCX, SCY, 0.5 * R_UNIT * SC * st["sc"], 0, 2 * math.pi)     # 真ん中の4分の1の境目（半径の半分）
    ctx.set_source_rgba(*hexrgb(GOLD, 0.16))
    ctx.fill_preserve()
    ctx.set_dash([9, 7])
    _stroke(ctx, 2.5, GOLD_D, 0.8)
    ctx.set_dash([])
    n = len(st["gid"])
    idx = np.arange(n)
    wob_x = 0.12 * SC * np.sin(2.3 * t + st["gid"])      # 揺れ（泳いでいる感じ）
    wob_y = 0.10 * SC * np.cos(1.9 * t + 1.7 * st["gid"])
    for i in np.argsort(st["gold"], kind="stable"):      # 金を上に描く
        if st["gone"][i]:
            continue
        wag = 0.45 * math.sin(2 * math.pi * (2.4 * t + st["gid"][i] * 0.37))
        draw_fish(ctx, float(st["fx"][i] + wob_x[i]), float(st["fy"][i] + wob_y[i]), float(st["ang"][i]), L_FISH, bool(st["gold"][i]), wag)
    if st["shark"] is not None:
        draw_shark(ctx, st["shark"][0], st["shark"][1], st["shark"][2], L_SHARK, st["shark"][3])
    for (ex, ey), age in st["flashes"]:                  # 食べられた1匹: 光って消える
        rad = 20 + 100 * ease_out(age / 0.5)
        al = 1 - clamp01(age / 0.5)
        ctx.arc(ex, ey, rad, 0, 2 * math.pi)
        _stroke(ctx, 5, "#fff6c2", 0.95 * al)
        for q in range(8):
            a_ = q * math.pi / 4 + 0.3
            ctx.move_to(ex + math.cos(a_) * (rad * 0.5), ey + math.sin(a_) * (rad * 0.5))
            ctx.line_to(ex + math.cos(a_) * (rad * 1.05), ey + math.sin(a_) * (rad * 1.05))
        _stroke(ctx, 4, "#ffffff", 0.95 * al)


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 24)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 16)
    ctx.clip()
    draw_water_card(ctx, t)
    ctx.restore()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 16)
    _stroke(ctx, 3.2, INK, 0.85)
    rrect(ctx, 76, 22, 430, 82, 12)                     # 題（左上）。冒頭の拡大で左が切れないよう x=88 から
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    text(ctx, "イワシ500匹の群れ", 96, 46, 40, INK, align="left")
    text(ctx, "たとえば、この1回の狩りでは", 96, 86, 26, PENCIL, align="left", bold=False)
    if t >= T_SH0:                                       # 数え（右上）
        st = hunt_state(t)
        a_ = ease_out((t - T_SH0) / 0.25)
        rrect(ctx, CARD_W - 440, 22, 410, 100, 12)
        ctx.set_source_rgba(*hexrgb("#c9f0dc", 0.95 * a_))
        ctx.fill()
        if t < T_HEND + 0.2:
            text(ctx, f"突っ込み {st['k'] + 1}回目", CARD_W - 424, 54, 34, INK, align="left", alpha=a_)
            text(ctx, f"食べられた {st['eaten']}匹（真ん中 {st['eaten_in']}匹）", CARD_W - 424, 98, 26, INK, align="left", bold=False, alpha=a_)
        else:
            text(ctx, f"この1回の狩り 突っ込み{N_SHOW}回", CARD_W - 424, 54, 30, INK, align="left", alpha=a_)
            text(ctx, f"食べられた{st['eaten']}匹・真ん中は{st['eaten_in']}匹", CARD_W - 424, 98, 28, INK, align="left", alpha=a_)
    if m >= 0.999:                                       # 下の札は 場面が定位置に着いてから（カードの下端が y=1450 を超えないため）
        a2 = clamp01((t - T_GO) / 0.3)
        if a2 > 0:
            rrect(ctx, 24, CARD_H - 72, 570, 52, 12)             # 色の見本（左下）
            ctx.set_source_rgba(*hexrgb(PAPER, 0.93 * a2))
            ctx.fill()
            draw_fish(ctx, 58, CARD_H - 46, 0.0, 34, True, a=a2)
            text(ctx, "金＝真ん中の4分の1", 92, CARD_H - 46, 26, INK, align="left", bold=False, alpha=a2)
            draw_fish(ctx, 362, CARD_H - 46, 0.0, 34, False, a=a2)
            text(ctx, "銀＝そのほか", 396, CARD_H - 46, 26, INK, align="left", bold=False, alpha=a2)
            rrect(ctx, CARD_W - 356, CARD_H - 72, 276, 52, 12)    # 絵は一部（右下）
            ctx.set_source_rgba(*hexrgb(PAPER, 0.93 * a2))
            ctx.fill()
            text(ctx, "絵は500匹の一部", CARD_W - 218, CARD_H - 46, 26, PENCIL, bold=False, alpha=a2)
    if T_SH0 <= t < PASS_T0[0] + P_FIRST:
        rrect(ctx, CARD_W - 200, 134, 170, 46, 12)
        ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
        ctx.fill()
        text(ctx, "スロー再生", CARD_W - 115, 157, 26, INK, bold=False)
    ctx.restore()


def scene_alpha(t):
    if t < T_D0:
        return 1.0
    return 1 - ease((t - T_D0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.20 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: 場面が寄ったところから引く（下端を基準に）
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


# ---------- 点の図（食べられた魚の場所） ----------
_DOTS = {}
_EV = {}


def events():
    """食べられた魚（狩りごとの突っ込みの回数まで）の 位置・真ん中か・狩りの番号"""
    if not _EV:
        m = results()["main"]
        keep = m["ev_m"] < m["n_pass"][m["ev_h"]]
        _EV.update(tx=m["ev_tx"][keep].astype(np.float64), ty=m["ev_ty"][keep].astype(np.float64),
                   inner=m["ev_inner"][keep], h=m["ev_h"][keep])
    return _EV


def bgra_(color, a):
    c = hexrgb(color)
    return np.array([c[2] * 255, c[1] * 255, c[0] * 255], np.float32) * a


def dot_surface(key, tx, ty, inner, R, m):
    """m 個ぶんまで積んだ点の図（点が重なるほど濃く）。単位円 → 半径 R px。外が青、真ん中（金）が上"""
    step = max(1, len(tx) // 90)
    kk = (key, int(m) // step if m < len(tx) else -1)
    if kk in _DOTS:
        return _DOTS[kk]
    if len(_DOTS) > 300:
        _DOTS.clear()
    size = int(2 * R + 12)
    mm = len(tx) if m >= len(tx) else (int(m) // step) * step
    px = np.clip((tx[:mm] * R + R + 6).astype(int), 1, size - 2)
    py = np.clip((ty[:mm] * R + R + 6).astype(int), 1, size - 2)
    inn = inner[:mm].astype(bool)
    rgba = np.zeros((size, size, 4), np.float32)                 # 事前に掛けた BGRA
    for sel, col in ((~inn, DOT_OUT), (inn, GOLD)):
        cnt = np.zeros((size, size), np.float32)
        np.add.at(cnt, (py[sel], px[sel]), 1.0)
        al = 1 - np.exp(-0.45 * cnt)
        rgba[:, :, :3] = rgba[:, :, :3] * (1 - al[:, :, None]) + bgra_(col, 1.0)[None, None, :] * al[:, :, None]
        rgba[:, :, 3] = rgba[:, :, 3] * (1 - al) + 255 * al
    buf = np.ascontiguousarray(np.clip(rgba, 0, 255).astype(np.uint8))
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, size, size, size * 4)
    _DOTS[kk] = (surf, buf)
    return _DOTS[kk]


def dots_alpha(t):
    if t < T_D0:
        return 0.0
    return ease((t - T_D0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_dots(ctx, t):
    a = dots_alpha(t)
    if a <= 0:
        return
    r = results()
    ev = events()
    n_ev = len(ev["tx"])
    pr = clamp01((t - T_D0 - 0.8) / (T_D1 - T_D0 - 0.8))
    m_rev = n_ev if pr >= 1 else int(n_ev * ease(pr))
    cx, cy, R = DOT_C[0], DOT_C[1], DOT_R
    ctx.arc(cx, cy, R, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#e4f3f9", 0.95 * a))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.8 * a)
    ctx.arc(cx, cy, 0.5 * R, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(GOLD, 0.16 * a))
    ctx.fill()
    surf, _ = dot_surface("ev", ev["tx"], ev["ty"], ev["inner"], R, m_rev)
    ctx.set_source_surface(surf, cx - R - 6, cy - R - 6)
    ctx.paint_with_alpha(a)
    ctx.arc(cx, cy, 0.5 * R, 0, 2 * math.pi)
    ctx.set_dash([8, 6])
    _stroke(ctx, 2.5, GOLD_D, 0.9 * a)
    ctx.set_dash([])
    text(ctx, "真ん中\n4分の1", cx, cy, 34, GOLD_D, alpha=a * 0.9)
    hh = N_HUNT if m_rev >= n_ev else (int(ev["h"][m_rev - 1]) + 1 if m_rev > 0 else 0)
    text(ctx, "食べられた魚の場所（1万回の狩りぶん）", 560, 628, 38, INK, alpha=a)
    text(ctx, f"点＝食べられた魚1匹　狩り {hh:,} / 10,000 回目", 560, 668, 26, PENCIL, bold=False, alpha=a)
    if t >= T_DN:
        u = ease_out((t - T_DN) / 0.3) * a
        cx2 = 790.0
        text(ctx, "食べられた魚のうち", cx2, 725, 34, INK, bold=False, alpha=u)
        text(ctx, "真ん中だった割合", cx2, 767, 34, INK, bold=False, alpha=u)
        text(ctx, p1(r["p"]), cx2, 860, 104, RED, alpha=u)
        text(ctx, "（中央値＝1万回の\nちょうど真ん中の値）", cx2, 945, 28, PENCIL, bold=False, alpha=u)
        text(ctx, "平等なら 25%", cx2, 992, 30, PENCIL, bold=False, alpha=u)
    if t >= T_DN2:
        u = ease_out((t - T_DN2) / 0.3) * a
        cx3 = 770.0
        text(ctx, "真ん中が1匹でも", cx3, 1052, 32, INK, bold=False, alpha=u)
        text(ctx, "食べられた狩りは", cx3, 1092, 32, INK, bold=False, alpha=u)
        text(ctx, once_in(r["st"]["frac_c"]), cx3, 1150, 38, RED, alpha=u)


# ---------- ひねり（突っ込みの回数別） ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    r = results()
    text(ctx, "突っ込みの回数別（同じ1万回の狩りの途中）", 560, 628, 38, INK, alpha=a)
    text(ctx, "真ん中の魚が1匹でも食べられた狩りの割合", 560, 670, 28, PENCIL, bold=False, alpha=a)
    ctx.move_to(80, TW_BASE)
    ctx.line_to(1010, TW_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    pr = ease(clamp01((t - T_TW - 0.8) / (T_TS1 - T_TW - 0.8)))
    for i, mm in enumerate(M_SHOW):
        s_ = r["by_m"][mm]
        x = TW_X[i]
        hgt = TW_H * s_["frac_c"] * pr
        rrect(ctx, x - 85, TW_BASE - hgt, 170, max(hgt, 1.0), 10)
        ctx.set_source_rgba(*hexrgb(DOT_OUT, 0.9 * a))
        ctx.fill()
        text(ctx, f"{pct(s_['frac_c'] * pr)}%", x, TW_BASE - hgt - 32, 48, RED, alpha=a)
        text(ctx, f"{mm}回", x, TW_BASE + 40, 40, INK, alpha=a)
    text(ctx, "食べられた魚のうち真ん中の割合（中央値）", 560, TW_BASE + 98, 28, PENCIL, bold=False, alpha=a)
    if t >= T_TS1:
        for i, mm in enumerate(M_SHOW):
            q = ease_out((t - T_TS1 - 0.1 * i) / 0.3) * a
            text(ctx, p1(r["by_m"][mm]["p_med"]), TW_X[i], TW_BASE + 148, 42, INK, alpha=q)


# ---------- 答え ----------

def answer_key():
    return answer_by_rule(results()["p"])


def reason_text():
    st = results()["st"]
    return (f"1回の狩りで、真ん中の1匹は\n{p1(st['d_c'])}の確率で食べられる。\n"
            f"端の1匹は {p1(st['d_e'])}の確率で食べられる。")


TW_Q = "では、狩りが長く続くと？"


def tw_a():
    r = results()
    return f"突っ込みが40回続くと、\n真ん中も食べられる狩りが {pct(r['by_m'][40]['frac_c'])}%になる。"


def tw_b():
    r = results()
    return f"食べられた魚のうち 真ん中は {p1(r['by_m'][10]['p_med'])}→{p1(r['by_m'][40]['p_med'])}に増える。"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 570, 1266, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 570, 1388, 26, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 570, 1238, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        text(ctx, tw_a(), 570, 1355, 36, RED, alpha=e)
        text(ctx, tw_b(), 570, 1435, 26, INK, bold=False, alpha=e)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に水の中の群れ（0秒目から泳ぎ、場面が寄った所から引く）"""
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


# ---------- 締め（3匹のイワシ） ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたがイワシなら、\n群れのどこを泳ぎますか？", 580, 800, 56, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 950, 36, INK, bold=False, alpha=r)
    ctx.save()                                                                  # 水のなかの3匹
    ctx.push_group()
    rrect(ctx, 90, 1010, 900, 430, 24)
    ctx.clip()
    ctx.translate(90, 1010)
    ctx.set_source_surface(water_bg(), -30, -100)
    ctx.paint()
    for i, (x, y, gold) in enumerate(((250, 150, False), (470, 270, True), (690, 150, False))):
        wag = 0.5 * math.sin(2 * math.pi * (2.2 * (t - T_Q) + i * 0.33))
        draw_fish(ctx, x + 6 * math.sin(1.3 * t + i), y + 5 * math.cos(1.1 * t + i), math.pi, 210, gold, wag)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    rrect(ctx, 90, 1010, 900, 430, 24)
    _stroke(ctx, 3.5, INK, 0.75 * q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_dots(ctx, t)
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
    for i in range(4):                                      # 冒頭: あわ ぽこ・ぽこ
        mx.add(0.1 + 0.5 * i, blip(520 + 70 * i, 0.07), 0.3)
    S = samples()
    for k in range(N_SHOW):                                 # 突っ込みごとに サメが通る音。食べられたら 光る音
        mx.add(PASS_T0[k] + 0.05, whoosh(min(PASS_DUR[k], 1.0)), 0.30 if k else 0.4)
        if S["recs"][k]["hit"] >= 0:
            tc = pass_geom(k)["t_cross"]
            mx.add(tc, bell(1318.5, 0.8), 0.40)
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # 点の図
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
    for i in range(4):
        mx.add(T_TS1 + 0.1 * i, bell([784.0, 880.0, 988.0, 1046.5][i], 0.8), 0.35)
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


def _pass_ref(pos, q, d, vrel, rd, lat, cfg):
    """pass_core と別の書き方（1匹ずつの普通のループ）。同じ1匹を選ぶか照合する"""
    best, bs = -1, 1e18
    for i in range(len(pos)):
        rx, ry = pos[i, 0] - q[0], pos[i, 1] - q[1]
        l = -rx * d[1] + ry * d[0]
        s = rx * d[0] + ry * d[1]
        D = cfg["fb"] * max(0.0, rd / vrel - lat[i])
        if abs(l) + D < cfg["w"] and s < bs:
            best, bs = i, s
    return best


def run_checks():
    r = results()
    m, st = r["main"], r["st"]
    p = r["p"]
    checks = []
    H_ = len(m["n_pass"])
    # (1) 条件
    checks.append(("真ん中の4分の1 = 125/500 = 25%（平等の基準）", N_INNER / N_FISH, 0.25, 0.0))
    for s_ in (0, 1, 2):
        a_, b_ = shape_ab(s_)
        checks.append((f"群れの面積が形によらず同じ（形{s_}）", a_ * b_ * math.pi, AREA, 1e-6))
    checks.append(("テンプレート: 単位円の中・500点", float(all(len(t) == N_FISH and np.sqrt((t ** 2).sum(1)).max() <= 1 + 1e-9 for t in templates())), 1.0, 0.0))
    for s_ in (0, 1, 2):
        checks.append((f"形の回数が3分の1ずつ（形{s_}）", float((m["shape"] == s_).mean()), 1 / 3, 0.02))
    checks.append(("群れの速さ U の平均が 1.5（0〜3 の一様）", float(m["U"].mean()), 1.5, 0.06))
    checks.append(("サメの k の平均が 3.25（1.5〜5 の一様）", float(m["k"].mean()), 3.25, 0.08))
    checks.append(("突っ込みの回数は 10〜40（平均 25）", float(m["n_pass"].min() >= P_MIN and m["n_pass"].max() <= P_MAX), 1.0, 0.0))
    checks.append(("突っ込みの回数の平均 25（10〜40の一様）", float(m["n_pass"].mean()), 25.0, 0.4))
    checks.append(("狩りの数 = 1万", float(H_), float(N_HUNT), 0.0))
    # (2) 数え方の整合（累計と、食べられた魚の一覧は 別の数え方）
    checks.append(("累計は増えるだけ（食べられた魚が消えて戻らない）", float((np.diff(m["cumE"].astype(int), axis=1) >= 0).all() and (np.diff(m["cumI"].astype(int), axis=1) >= 0).all()), 1.0, 0.0))
    checks.append(("1回の突っ込みで食べられるのは 1匹まで", float((np.diff(m["cumE"].astype(int), axis=1) <= 1).all()), 1.0, 0.0))
    checks.append(("真ん中で食べられた数 ≤ 食べられた数", float((m["cumI"] <= m["cumE"]).all()), 1.0, 0.0))
    checks.append(("食べられた魚の一覧の数 = 累計の合計（40回まで）", float(len(m["ev_h"])), float(m["cumE"][:, -1].sum()), 0.0))
    checks.append(("食べられた魚の一覧の真ん中の数 = 累計の合計", float(m["ev_inner"].sum()), float(m["cumI"][:, -1].sum()), 0.0))
    # 一覧から p を数え直す（累計とは別の道）
    keep = m["ev_m"] < m["n_pass"][m["ev_h"]]
    Eh = np.bincount(m["ev_h"][keep], minlength=H_)
    Ih = np.bincount(m["ev_h"][keep][m["ev_inner"][keep]], minlength=H_)
    has = Eh > 0
    checks.append(("p（中央値）を 食べられた魚の一覧から数え直しても同じ", float(np.median(Ih[has] / Eh[has])), p, 1e-12))
    checks.append(("真ん中が1匹でも食べられた狩りの割合 を 一覧から数え直しても同じ", float((Ih > 0).mean()), st["frac_c"], 1e-12))
    checks.append(("1匹あたり食べられる確率（真ん中）を 一覧から数え直しても同じ", float(Ih.sum() / (N_INNER * H_)), st["d_c"], 1e-12))
    checks.append(("1匹あたり食べられる確率（端）を 一覧から数え直しても同じ", float((Eh - Ih).sum() / ((N_FISH - N_INNER) * H_)), st["d_e"], 1e-12))
    checks.append(("真ん中の魚は 位置が中心に近い（食べられた真ん中の魚は 半径 0.6 未満）", float(m["ev_rn"][m["ev_inner"]].max() < 0.6), 1.0, 0.0))
    # (3) 突っ込み1回の計算を、別の書き方で照合
    rng = np.random.default_rng(99)
    agree = 0
    for _ in range(300):
        par = draw_params(rng)
        P0, _, _ = school(par)
        n_ = int(rng.integers(200, 500))
        pos = P0[:n_] * math.sqrt(n_ / N_FISH)
        al = rng.uniform(-math.pi / 2, math.pi / 2)
        v = np.array([3 * par["k"] * math.cos(al) - par["U"], 3 * par["k"] * math.sin(al)])
        vr = float(np.hypot(*v))
        dd = v / vr
        q = rng.normal(0, SIGMA_AIM * R_UNIT, 2)
        rd = rng.uniform(RD_MIN, RD_MAX)
        lat = np.where(rng.random(n_) < P_FAST, LAT_FAST, LAT_SLOW)
        a1 = pass_core(pos, q, dd, vr, rd, lat, CFG0)[0]
        a2 = _pass_ref(pos, q, dd, vr, rd, lat, CFG0)
        agree += int(a1 == a2)
    checks.append(("突っ込み1回: 速い計算と 1匹ずつのループが同じ魚を選ぶ（300回）", float(agree), 300.0, 0.0))
    z = run_hunt(np.random.default_rng([SEED_MAIN, 0]), dict(CFG0, w=0.0))
    checks.append(("口の幅0なら 何も食べられない", float(z["cumE"][-1]), 0.0, 0.0))
    # (4) 数字の向き（ひねり）
    fm = [r["by_m"][k_]["frac_c"] for k_ in M_SHOW]
    checks.append(("突っ込みが増えるほど 真ん中が食べられた狩りの割合が増える", float(all(fm[i] < fm[i + 1] for i in range(3))), 1.0, 0.0))
    pm = [r["by_m"][k_]["p_med"] for k_ in M_SHOW]
    checks.append(("40回の p（中央値）は 10回より大きい（ひねりの文）", float(pm[3] > pm[0]), 1.0, 0.0))
    checks.append(("40回の p と 30回の p の差が 2ポイント以内（頭打ちの文）", float(abs(pm[3] - pm[2]) <= 0.02), 1.0, 0.0))
    checks.append(("真ん中の1匹のほうが 端の1匹より 食べられにくい（理由の文）", float(st["d_c"] < st["d_e"]), 1.0, 0.0))
    # (5) 答え
    key = answer_by_rule(p)
    checks.append(("規則の答え = center（真ん中のほうが安全）", float(key == "center"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B（2番目）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号の並び: ほぼ同じ・真ん中のほうが安全・端のほうが安全 の順", float(LABELS == ["ほぼ同じ", "真ん中のほうが安全", "端のほうが安全"]), 1.0, 0.0))
    for v_, k_ in ((0.10, "center"), (0.15, "center"), (0.25, "same"), (0.35, "edge")):
        checks.append((f"規則の道具: p={v_:.2f} → {k_}", float(answer_by_rule(v_) == k_), 1.0, 0.0))
    # (6) 見本は1万回の中の1回そのもの
    S = samples()
    h = S["h"]
    checks.append(("見本: 記録し直した累計 = 1万回の記録（食べられた数）", float(S["rec"]["cumE"][N_SHOW - 1]), float(m["cumE"][h, N_SHOW - 1]), 0.0))
    checks.append(("見本: 記録し直した累計 = 1万回の記録（40回まで全部）", float(np.array_equal(S["rec"]["cumE"], m["cumE"][h])), 1.0, 0.0))
    checks.append(("見本: 突っ込みは10回", float(m["n_pass"][h]), float(N_SHOW), 0.0))
    checks.append(("見本: 真ん中は食べられていない（画面の数え = 1万回の記録）", float(S["rec"]["cumI"][N_SHOW - 1]), float(m["cumI"][h, N_SHOW - 1]), 0.0))
    stt = hunt_state(T_HEND)
    checks.append(("見本: 画面の数え（食べられた匹数）= 1万回の記録", float(stt["eaten"]), float(m["cumE"][h, N_SHOW - 1]), 0.0))
    checks.append(("見本: 絵に描く魚は 500匹の一部（約125＋食べられる魚）", float(120 <= int(S["drawn"].sum()) <= 140), 1.0, 0.0))
    checks.append(("見本: 食べられる魚はすべて絵に描かれる", float(all(S["drawn"][rc["hit"]] for rc in S["recs"] if rc["hit"] >= 0)), 1.0, 0.0))
    checks.append(("見本: 1回目の突っ込みのスローは 1.5秒以上", float(P_FIRST >= 1.5), 1.0, 0.0))
    # (7) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    checks.append(("問い3行: 3行の文字の大きさが同じ（同じ s3 で描く）", float(len(set([s3] * 3)) == 1), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (8) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("結果が見える時間: 見本（10回の突っ込みのあと 次の場面まで）3秒以上", float(T_D0 - T_HEND >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 点の図の最後の数字 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 棒グラフの数字 3秒以上", float(T_Q - T_TS1 >= 3.0), 1.0, 0.0))
    checks.append(("突っ込み1回の長さは どれも 0.6秒以上（途中で切らない・見える）", float(min(PASS_DUR) >= 0.6), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (9) 冒頭の動き
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
    st = hunt_state(T_HEND)
    print(f"長さ {DURATION:.1f}秒  突っ込み {T_SH0:.1f}〜{T_HEND:.1f}  点の図 {T_D0:.1f}-{T_D1:.1f}  数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: 狩り #{S['h']}  突っ込み{N_SHOW}回  食べられた {st['eaten']}匹（真ん中 {st['eaten_in']}匹）  描く魚 {int(S['drawn'].sum())}匹  突っ込み1回 {P_FIRST:.2f}秒 + {P_REST:.2f}秒×{N_SHOW - 1}")
    print(f"  問い3行の文字 {min(big3_size(820.0), 92.0):.0f}px  最長行 {max(core.text_width(l, min(big3_size(820.0), 92.0)) for l in BIG_Q3):.0f}px")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a().replace("\n", ""), "|", tw_b())
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, PASS_T0[0] + 0.5, PASS_T0[0] + 1.0, PASS_T0[0] + 1.5, PASS_T0[1] + 0.3, PASS_T0[2] + 0.3,
              PASS_T0[5] + 0.3, T_HEND - 0.2, T_HEND + 1.5, T_D0 + 1.5, T_D1 - 0.2, T_DN + 1.2, T_DN2 + 1.2, T_REV + 0.9, T_ANS2 + 0.6,
              T_TW + 0.8, T_TW + 2.4, T_TS1 + 1.2, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
