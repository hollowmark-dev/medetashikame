"""冬、遠くの電車の音がよく聞こえるのは、昼？夜？ 同じ距離・同じ日の昼と夜をくらべて1万回。— 2026-10-23 作成（公開予定 10/30）

モデル（音の線を光線追跡で曲げて進める。風は入れない＝無風。1回ごとに距離・気温・逆転層の強さと厚さ・音源の高さをでたらめに変える）
  音の速さ : c = 331.5 ＋ 0.6 × 気温（℃）（m/秒）。20℃で343.5。（Wikipedia「音速」の近似式。教科書の約343 m/秒）
  線の進み方 : 気温が高さで変わる空気の中で、線は音の速さが遅いほうへ曲がる（dθ/dx = −(1/c)·dc/dz。θ は水平からの角度）。
            地面はぜんぶはね返す（仮定。実際は草や雪で少し吸われる）。気温の分布は折れ線にして、1枚の層の中の線は円の弧になる
            （スネルの法則 cosθ/c ＝ 一定）。その水平距離は閉じた式で出る。1歩ずつ進める計算（0.25m刻み）と照合してある。
  昼（冬の晴れた昼） : 地面付近の気温 5〜12℃（仮定）。高さ100mで 0.6〜1.0℃ずつ下がる（標準大気は0.65℃/100m）。
            地面から10mまでは もっと急（最大 100mで3℃・仮定）。
  夜（冬の晴れた夜・風が弱い）: 同じ日の昼より 6〜12℃低い（仮定）。地面の近くが冷えて上ほど暖かい層（接地逆転層）ができる。
            厚さ 30〜120 m（鹿島の観測で約60m: 気象学会「天気」1991「鹿島で観測された乱流的接地逆転層について」
            https://www.metsoc.jp/tenki/pdf/1991/1991_03_0151.pdf 。ほかに 電力中央研究所 1975 報告 275006 は放射性逆転層の厚さが通常約300m・
            上限は 50×気温の日較差 としている。ここでは地面に近い下の部分だけを使う）。
            地面と層の上の気温差 2〜7℃（仮定。公的な観測で幅を確かめられなかった）。厚さ1mあたり0.12℃（100mで12℃）は超えない（仮定）。
            層の上は 100mで0.65℃ずつ下がる。気温は下から 0 → 0.55×差（厚さの3割）→ 差（厚さ）と折れ線で上がる。
  音源 : 地面から 3.5〜6 m（仮定。箱の高さより上）。距離 1〜3 km（でたらめ）。
  音の線 : 音源から水平 ±10°に、1万本（一様な向き）。
  聞く人のまわり（箱） : 地面から 3m まで・距離の幅 ±50m（仮定）。
  測るもの : 届いた本数 ＝ 箱の中を通った線の水平の長さの合計 ÷ 箱の幅（100m）。箱を端から端まで通れば1本。
            音が曲がらないときの本数 6/(距離×線の間隔)（直接の線と地面ではね返った線）と同じ物差しで比べられる。
  1回ごとの比べっこ : 同じ距離・同じ日の昼と夜（気温の差だけ変える）。1万回。
  ひねり   : 「では、音が曲がらなかったら？」 気温が高さによらない空気（ほぼ一様）で同じ1万回。風は入れない（入れるなら仮定の追加が要る）。
  入れていないもの : 風・空気のゆらぎ（影の中にも少し音が回りこむ）・地面の吸収・建物や地形・雨や雪。
            ここでの「昼は0本」は「線が届かない」の意味で、実際の昼は 影の中でも少し届く。

問い: 「冬、遠くの電車の音が / よく聞こえるのは、昼？夜？」 夜 ／ ほぼ同じ ／ 昼（並びは ORDER・LABELS・CORRECT で変える）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「夜のほうが届いた本数が多かった回」の割合 p と、届いた量の比（夜÷昼。0で割らないよう両方に1を足す）の真ん中の値 r で、
      p ≥ 60% かつ r ≥ 1.5 なら「夜」、p ≤ 40% かつ r ≤ 1/1.5 なら「昼」、それ以外は「ほぼ同じ」。
      結果がどれでも、そのまま答えにする。同数（0本どうし）は『夜が多い』に入れない。
記号: A 夜・B ほぼ同じ・C 昼（統括の指示で正解の夜を A にした。自然な並びは 昼・ほぼ同じ・夜）で、正解は A。最後に並びを決めるときは、ORDER・LABELS・CORRECT と comment.txt を入れ替えるだけ。
締め: 「あなたの家からは、夜に何の音が聞こえますか？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（距離約2km・昼は届かず夜は中くらいの本数の回）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
見本の絵: 描く線は27本だけ（1万本のごく一部）。赤い線は、箱を通った線の中から3本。高さは約20倍にのばして描いている（横は距離を446pxに縮める）。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "yoru-oto"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000                                   # 比べっこの回数（同じ距離・同じ日の昼と夜）
N_RAY = 10000                                     # 1回ごとに音源から出す音の線の本数
TH_MAX = math.radians(10.0)                       # 線の出す向き: 水平から ±10°（一様）。これより急な線は遠くの地面に届かない
BOX_H, BOX_W = 3.0, 50.0                          # 聞く人のまわり: 地面から3mまで・距離の幅 ±50 m（仮定）
ZS_RANGE = (3.5, 6.0)                             # 音源（電車）の高さ（m）。仮定（箱の高さ3mより上にして、線が最初は箱の上から出るようにする）
R_RANGE = (1000.0, 3000.0)                        # 電車までの距離（m）。仮定
T_DAY_G = (5.0, 12.0)                             # 冬の昼の地面付近の気温（℃）。仮定
DT_DAY_NIGHT = (6.0, 12.0)                        # 同じ日の、昼の気温から夜の気温への下がり幅（℃）。仮定
LAPSE = (0.006, 0.010)                            # 昼: 高さ1mあたりの気温低下（K/m）＝100mで0.6〜1.0℃（標準大気は0.65℃/100m）
LAPSE_NEAR = 0.030                                # 昼: 地面から10mまでは もっと急なこともある（最大 100mあたり3℃・仮定）
H_INV = (30.0, 120.0)                             # 夜: 地面の近くが冷えて上ほど暖かい層の厚さ（m）。鹿島の観測で約60m（天気 1991）
DT_INV = (2.0, 7.0)                               # 夜: 地面と層の上の気温差（℃）。仮定（公的な観測で幅を確かめられなかった）
DT_INV_PER_M = 0.12                               # 夜: 気温差が 厚さ1mあたり0.12℃（100mで12℃）を超えないようにする（仮定）
LAPSE_TOP = 0.0065                                # 夜: 層より上は100mで0.65℃ずつ下がる
Z_TOP = 1500.0

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_RATIO = 0.60, 0.40, 1.5
NAMES = ["昼", "ほぼ同じ", "夜"]                  # 規則での番号 0・1・2


def answer_by_rule(p_night, r_med):
    """p_night = 夜のほうが多く届いた回の割合、r_med = 届いた量の比（夜÷昼）の真ん中の値。返り値: NAMES の番号"""
    if p_night >= RULE_HI and r_med >= RULE_RATIO:
        return 2                                  # 夜
    if p_night <= RULE_LO and r_med <= 1.0 / RULE_RATIO:
        return 0                                  # 昼
    return 1                                      # ほぼ同じ


THETA = np.linspace(-TH_MAX, TH_MAX, N_RAY)


def c_of_T(T):
    """音の速さ（m/秒）＝ 331.5 ＋ 0.6 × 気温（℃）"""
    return 331.5 + 0.6 * np.asarray(T, float)


def make_profile(rng, kind, t_ground):
    """kind: 'day' 昼 / 'night' 夜 / 'flat' 気温が高さによらない（ほとんど）。折れ線の気温分布"""
    if kind == "day":
        g = rng.uniform(*LAPSE)
        g0 = rng.uniform(g, LAPSE_NEAR)
        zk = np.array([0.0, 10.0, Z_TOP])
        tk = np.array([t_ground, t_ground - g0 * 10, t_ground - g0 * 10 - g * (Z_TOP - 10)])
        info = dict(g=g, g0=g0)
    elif kind == "night":
        h = rng.uniform(*H_INV)
        dt = rng.uniform(DT_INV[0], min(DT_INV[1], DT_INV_PER_M * h))
        zk = np.array([0.0, 0.3 * h, h, Z_TOP])
        tk = np.array([t_ground, t_ground + 0.55 * dt, t_ground + dt, t_ground + dt - LAPSE_TOP * (Z_TOP - h)])
        info = dict(h=h, dt=dt)
    else:                                         # flat: 音が曲がらない空気（比べるための基準）。わずかに下がるだけにして計算の式を同じにする
        zk = np.array([0.0, 10.0, Z_TOP])
        tk = np.array([t_ground, t_ground - 1e-7, t_ground - 1e-5])
        info = {}
    return dict(kind=kind, zk=zk, ck=c_of_T(tk), tk=tk, **info)


def c_at(P, z):
    return np.interp(z, P["zk"], P["ck"])


def x_between(P, k, za, zb):
    """ある線（k = cosθ / c が一定）が高さ za から zb（za<zb）まで、折り返さずに進む間の水平の距離（m）。
    折れ線の気温分布では、1枚の層の中の線は円の弧になり、水平距離は閉じた式で出る:
    c が z で直線のとき  x = (√(1−u1²) − √(1−u2²)) / (k·g)   （u = k·c, g = dc/dz）"""
    zk, ck = P["zk"], P["ck"]
    tot = np.zeros(np.broadcast(k, za, zb).shape)
    for i in range(len(zk) - 1):
        lo = np.maximum(za, zk[i])
        hi = np.minimum(zb, zk[i + 1])
        m = hi > lo
        if not np.any(m):
            continue
        g = (ck[i + 1] - ck[i]) / (zk[i + 1] - zk[i])
        clo, chi = ck[i] + g * (lo - zk[i]), ck[i] + g * (hi - zk[i])
        ulo, uhi = np.minimum(1.0, k * clo), np.minimum(1.0, k * chi)
        slo, shi = np.sqrt(np.maximum(0, 1 - ulo ** 2)), np.sqrt(np.maximum(0, 1 - uhi ** 2))
        if abs(g) > 1e-12:
            d = np.abs(slo - shi) / (k * abs(g))
        else:
            d = ulo / np.maximum(slo, 1e-9) * (hi - lo)
        tot = tot + np.where(m, d, 0.0)
    return tot


J_LOOP = 8


def box_overlap(P, zs, R, th=THETA):
    """音源（高さ zs）から出した線ごとに、聞く人のまわりの箱（距離 R±BOX_W・地面から BOX_H まで）の中を
    通る水平の長さ（m）。線は 地面ではね返る（全部反射）。
    線は「いちばん低くなる点（地面か、地面の上で水平になる点）」のまわりで箱の高さ以下になる。
    昼は戻ってくる線が1回きり、夜は 地面と最高点のあいだを往復（周期 Λ）するので、箱に重なる分を足す"""
    cs = c_at(P, zs)
    k = np.cos(th) / cs                           # スネルの法則: cosθ / c は線ごとに一定
    zk, ck = P["zk"], P["ck"]
    lo_w, hi_w = R - BOX_W, R + BOX_W
    inv = 1.0 / k
    zs_a = np.full_like(k, zs)
    if P["kind"] != "night":                      # 昼（上ほど冷たい）: 下向きに出た線だけが一度さがって戻る
        zn = np.where(inv <= ck[0], 0.0, np.interp(-inv, -ck, zk))      # 最下点（地面に着かないなら、水平になる高さ）
        zn = np.minimum(zn, zs)
        xn = x_between(P, k, zn, zs_a)
        hb = x_between(P, k, zn, np.full_like(k, BOX_H))
        ov = np.clip(np.minimum(hi_w, xn + hb) - np.maximum(lo_w, xn - hb), 0, None)
        return np.where((th < 0) & (zn <= BOX_H), ov, 0.0)
    i_h = 2                                       # 夜: 気温が上がり続ける層（地面〜層の上 H）
    trapped = inv <= ck[i_h]                      # 層の中で折り返す線だけが、層に閉じこめられる
    ztop = np.maximum(np.interp(inv, ck[:i_h + 1], zk[:i_h + 1]), zs)
    zeros = np.zeros_like(k)
    xt = x_between(P, k, zeros, ztop)             # 地面 → 最高点
    lam = np.maximum(2 * xt, 1e-6)                # 往復の周期
    xn = np.where(th > 0, x_between(P, k, zs_a, ztop) + xt, x_between(P, k, zeros, zs_a))   # 最初に地面に着く所
    hb = x_between(P, k, zeros, np.minimum(BOX_H, ztop))
    m0 = np.maximum(0, np.floor((lo_w - hb - xn) / lam))
    ov = np.zeros(len(th))
    for j in range(J_LOOP):
        xe = xn + (m0 + j) * lam
        ov += np.clip(np.minimum(hi_w, xe + hb) - np.maximum(lo_w, xe - hb), 0, None)
    many = (2 * BOX_W + 2 * hb) / lam + 2 > J_LOOP     # 箱の中で何度も往復する線は、箱の中にいる割合で近似
    duty = np.where(xn - hb <= lo_w, 2 * BOX_W * (2 * hb / lam), 0.0)
    ov = np.where(many, duty, ov)
    return np.where(trapped, ov, 0.0)


def count_rays(P, zs, R):
    """届いた本数（目安）＝ 箱の中を通った水平の長さの合計 ÷ 箱の幅。
    箱の中を端から端まで通った線が1本、というふうに数える（斜めに突っ切る線や、一部だけ通る線は割って足す）。
    どの線も同じ重みなので、音が曲がらないときの本数 6/(R×線の間隔) と同じ物差しで比べられる"""
    return float(box_overlap(P, zs, R).sum() / (2 * BOX_W))


def trace(P, zs, th, x_end, dx=2.0):
    """線を実際に1歩ずつ進める（ふつうの光線追跡）。dθ/dx = −(1/c)·dc/dz、dz/dx = tanθ。地面ではね返る。
    返り値: 各 dx ごとの高さ z（線 × 位置）。P=None なら曲がらない（気温が一様）"""
    th = np.asarray(th, float)
    n = int(round(x_end / dx)) + 1
    zz = np.zeros((len(th), n))
    z = np.full(len(th), float(zs))
    a = th.copy()
    zz[:, 0] = z
    if P is not None:
        zk, ck = P["zk"], P["ck"]
        gk = np.diff(ck) / np.diff(zk)

        def dcdz(zq):
            return gk[np.clip(np.searchsorted(zk, zq, side="right") - 1, 0, len(gk) - 1)]
    for i in range(1, n):
        if P is None:
            z = z + np.tan(a) * dx
        else:
            da = -dcdz(z) / c_at(P, z)
            am = a + da * dx / 2
            zm = np.abs(z + np.tan(a) * dx / 2)
            z = z + np.tan(am) * dx
            a = a - dcdz(zm) / c_at(P, zm) * dx
        neg = z < 0
        z = np.where(neg, -z, z)
        a = np.where(neg, -a, a)
        zz[:, i] = z
    return zz


def trace_flags(P, zs, R, th, dx=0.2):
    """trace で歩いて、箱の中を通った線の真偽（閉じた式の照合用）"""
    zz = trace(P, zs, th, R + BOX_W + dx, dx)
    xs = np.arange(zz.shape[1]) * dx
    m = (xs >= R - BOX_W) & (xs <= R + BOX_W)
    return (zz[:, m] <= BOX_H).any(1)


def trial_params(seed, i):
    rng = np.random.default_rng([seed, i])
    t_day = float(rng.uniform(*T_DAY_G))
    r = float(rng.uniform(*R_RANGE))
    zs = float(rng.uniform(*ZS_RANGE))
    t_night = t_day - float(rng.uniform(*DT_DAY_NIGHT))
    pd_ = make_profile(rng, "day", t_day)
    pn_ = make_profile(rng, "night", t_night)
    pf_ = make_profile(rng, "flat", t_day)
    return dict(R=r, zs=zs, day=pd_, night=pn_, flat=pf_, t_day=t_day, t_night=t_night)


def trial(seed, i):
    q = trial_params(seed, i)
    return (q["R"], q["zs"], count_rays(q["day"], q["zs"], q["R"]), count_rays(q["night"], q["zs"], q["R"]),
            count_rays(q["flat"], q["zs"], q["R"]), q["day"]["g"], q["day"]["g0"], q["night"]["h"], q["night"]["dt"],
            q["t_day"], q["t_night"])


SEED_MAIN = 20261030
KEYS = ["R", "zs", "n_day", "n_night", "n_flat", "g", "g0", "h", "dt", "t_day", "t_night"]
_RES = None


def results():
    global _RES
    if _RES is None:
        cache = OUT / "cache" / f"model_{SEED_MAIN}_v2.npz"
        if cache.exists():
            _RES = dict(np.load(cache))
        else:
            import time
            t0 = time.time()
            rows = []
            for i in range(N_TRIAL):
                rows.append(trial(SEED_MAIN, i))
                if i % 1000 == 999:
                    print(f"  モデル {i + 1}/{N_TRIAL}回  {time.time() - t0:.0f}秒", flush=True)
            a = np.array(rows, float)
            _RES = {k: a[:, j] for j, k in enumerate(KEYS)}
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **_RES)
    return _RES


def stats(r):
    nd, nn, nf = r["n_day"], r["n_night"], r["n_flat"]
    ratio = (nn + 1.0) / (nd + 1.0)
    return dict(p_night=float(np.mean(nn > nd)), n_night_more=int(np.sum(nn > nd)), n_day_more=int(np.sum(nd > nn)),
                n_tie=int(np.sum(nd == nn)), r_med=float(np.median(ratio)), ratio_q=np.percentile(ratio, [10, 25, 75, 90]),
                nd_med=float(np.median(nd)), nn_med=float(np.median(nn)), nf_med=float(np.median(nf)),
                nd_mean=float(nd.mean()), nn_mean=float(nn.mean()), nf_mean=float(nf.mean()),
                day_zero=float(np.mean(nd < 0.5)), day_some=float(np.mean(nd >= 0.5)),
                nn_q=np.percentile(nn, [5, 25, 75, 95]))


def shown():
    return stats(results())


def by_distance(edges=(1000, 1250, 1500, 2000, 3000.0001)):
    r = results()
    out = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (r["R"] >= a) & (r["R"] < b)
        out.append(dict(lo=a, hi=b, n=int(m.sum()), day_some=float(np.mean(r["n_day"][m] >= 0.5)),
                        nd_med=float(np.median(r["n_day"][m])), nn_med=float(np.median(r["n_night"][m])),
                        nf_med=float(np.median(r["n_flat"][m])), p_night=float(np.mean(r["n_night"][m] > r["n_day"][m]))))
    return out


def report():
    r = results()
    sh = stats(r)
    print(f"夜のほうが多く届いた {sh['p_night']:.4f}（{sh['n_night_more']}回 / 昼のほうが多い {sh['n_day_more']}回 / 同じ {sh['n_tie']}回）"
          f"  量の比（夜÷昼）の真ん中 {sh['r_med']:.1f}  10/25/75/90% {np.round(sh['ratio_q'], 1)}   答え {NAMES[answer_by_rule(sh['p_night'], sh['r_med'])]}")
    print(f"  届いた本数 真ん中: 昼 {sh['nd_med']:.1f} / 夜 {sh['nn_med']:.0f} / 音が曲がらない空気 {sh['nf_med']:.0f}   平均: 昼 {sh['nd_mean']:.1f} / 夜 {sh['nn_mean']:.0f} / 曲がらない {sh['nf_mean']:.0f}")
    print(f"  昼に0.5本未満（ほぼ届かない）の回 {sh['day_zero']:.3f}   夜の本数 5/25/75/95% {np.round(sh['nn_q'])}")
    for d in by_distance():
        print(f"  {d['lo']:.0f}〜{d['hi']:.0f}m ({d['n']}回): 昼に届いた回 {d['day_some']:.3f}  昼の真ん中 {d['nd_med']:.1f}  夜の真ん中 {d['nn_med']:.0f}  曲がらない {d['nf_med']:.0f}  夜が多い {d['p_night']:.3f}")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（1回ぶん）を選ぶ
# =====================================================================
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 距離 1950〜2050 m（動画に「2km」と出す）、昼は ほぼ届かない（0.5本未満）、夜の層の厚さ 50〜66 m・気温差 3〜5.5℃
    （絵の高さに収まる）、音源の高さ 3.5〜5 m。その中で、夜の本数が 1万回の真ん中の値に近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    sh = shown()
    ok = ((r["R"] >= 1950) & (r["R"] <= 2050) & (r["n_day"] < 0.5) & (r["h"] >= 50) & (r["h"] <= 66)
          & (r["dt"] >= 3.0) & (r["dt"] <= 5.5) & (r["zs"] >= 3.5) & (r["zs"] <= 5.0))
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    sc = np.abs(r["n_night"][cand] - sh["nn_med"]) / 200.0 + np.abs(r["R"][cand] - 2000.0) / 30.0
    best = int(cand[int(np.argmin(sc))])
    q = trial_params(SEED_MAIN, best)
    nd, nn, nf = (count_rays(q[k], q["zs"], q["R"]) for k in ("day", "night", "flat"))
    assert abs(nn - r["n_night"][best]) < 1e-6 and abs(nd - r["n_day"][best]) < 1e-6
    _SAMPLE = dict(i=best, q=q, R=q["R"], zs=q["zs"], n_day=nd, n_night=nn, n_flat=nf)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    q = s["q"]
    print("見本", s["i"], f"距離 {s['R']:.0f}m 音源の高さ {s['zs']:.2f}m  昼 {s['n_day']:.1f}本 / 夜 {s['n_night']:.0f}本 / 曲がらない {s['n_flat']:.0f}本",
          f" 夜: 厚さ {q['night']['h']:.0f}m 差 {q['night']['dt']:.1f}℃  昼: 100mあたり {q['day']['g'] * 100:.2f}℃ 近く {q['day']['g0'] * 100:.2f}℃  気温 昼{q['t_day']:.1f} 夜{q['t_night']:.1f}")
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, stills, check_true  # noqa: E402

note.use()
note.DATE = "10.30"                               # 日付欄（公開予定日）

COL_N, INK_N = "#8fbbe8", "#2f63a8"               # 夜（青）
COL_D, INK_D = "#f4ad6a", "#b8601a"               # 昼（橙）
SKIN = "#f6dcc6"
RAY = "#1d3a7a"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
BEND = 1.4                                        # まっすぐな線が、空気の温度で曲がるまで
T_CAP2 = T_GO + 3.2                               # 2つ目の説明
T_ARR = T_GO + 3.6                                # 届いた本数の数え始め
CNT_LEN = 1.8
RACE_LEN = 8.4                                    # T_GO から1万回のマス目まで
BIG_Q = ["冬、遠くの電車の音が", "よく聞こえるのは、昼？夜？"]
DETAIL = "電車まで 1〜3km。昼と夜をくらべます"
ORDER = [2, 1, 0]                                 # 画面の A・B・C に並べる NAMES の番号（夜・ほぼ同じ・昼）。正解の夜を A にした（統括の指示）
LABELS = [NAMES[i] for i in ORDER]
CORRECT = 0                                       # answer_by_rule で計算結果から決めた答え（画面での位置）。ずれたら run_checks が止める

# ---------- 場面（昼と夜を上下に並べる） ----------
PX0, PW, PH = 108.0, 880.0, 430.0                 # 枠の左・幅・高さ
P_TOPS = (700.0, 1150.0)                          # 昼・夜の枠の上
SKY_H = 374.0                                     # 空の高さ（枠の中。そのしたは地面）
X_ORG, X_END = 262.0, 652.0                       # 電車の先頭と、聞く人（枠の左から）
X_PERSON, X_HOUSE = 704.0, 752.0
ZPX = 5.5                                         # 高さ1mぶんのpx（横は 距離 R を 446px に縮める。高さを約20倍にのばして描く）
DISP_TH = np.radians(5.0 * np.sign(np.linspace(-1, 1, 27)) * np.abs(np.linspace(-1, 1, 27)) ** 1.8)   # 描く線の向き（27本）
PANEL_IDX = {"day": 0, "night": 1}
PNAME = {"day": "昼", "night": "夜"}
PSUB = {"day": "地面が暖かく、上ほど冷たい", "night": "地面の近くが冷たく、上が暖かい"}

_DISP = None


def display():
    """描く線: まっすぐな線（気温が一様）・昼・夜の線を、同じ向きで1歩ずつ進めたもの。夜は、箱に届いた線を3本、赤で足す"""
    global _DISP
    if _DISP is not None:
        return _DISP
    s = sample()
    q, R, zs = s["q"], s["R"], s["zs"]
    dx = R / 160.0
    out = dict(R=R, zs=zs, dx=dx)
    out["flat"] = trace(None, zs, DISP_TH, R, dx)
    out["day"] = trace(q["day"], zs, DISP_TH, R, dx)
    out["night"] = trace(q["night"], zs, DISP_TH, R, dx)
    ov = box_overlap(q["night"], zs, R)
    pick = []
    for target in (-3.1, 3.2, 5.1):                    # 箱を通った線のうち、この向きにいちばん近い線（地面すれすれでなく、弧が見える線）
        ok = np.nonzero(ov > 50)[0]
        j = int(ok[np.argmin(np.abs(np.degrees(THETA[ok]) - target))])
        pick.append(j)
    pick.sort(key=lambda j: THETA[j])
    out["red_idx"] = pick
    out["red"] = trace(q["night"], zs, THETA[pick], R, dx)
    out["red_flat"] = trace(None, zs, THETA[pick], R, dx)
    _DISP = out
    return out


def smooth_s(x):
    x = clamp01(x)
    return x * x * (3 - 2 * x)


# ---------- 絵: 人 ----------

def _limb(ctx, pts, w, col, ink=INK, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink, a))
    ctx.set_line_width(w + 3.6)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def draw_person(ctx, X, Y, h, look, phase=0.0, amp=0.0, a=1.0):
    """正面の人。足元が (X, Y)。h は背の高さ(px)"""
    if a <= 0:
        return
    s = h / 170.0
    ctx.save()
    ctx.translate(X, Y)
    ctx.scale(s, s)
    ctx.save()
    ctx.scale(1, 0.22)
    ctx.arc(0, 0, 30, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.15, 0.13, 0.1, 0.14)
    ctx.fill()
    bob = 2.4 * amp * abs(math.sin(phase))
    hip = -80.0 - bob
    for j in (0, 1):                                    # 足
        sg = -1 if j == 0 else 1
        ph = phase + j * math.pi
        lift = max(0.0, math.sin(ph)) * amp * 9.0
        fx = sg * (9.0 + 2.0 * amp * math.cos(ph))
        fy = -lift + 3.0 * amp * math.sin(ph)
        _limb(ctx, [(sg * 7.5, hip), (fx, fy - 4)], 14, look["pants"])
        fill(ctx, INK)
        ctx.save()
        ctx.translate(fx + sg * 1.5, fy - 1.5)
        ctx.scale(1.0, 0.5)
        ctx.arc(0, 0, 11.0, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill()
    if look["style"] == 1:                              # 長い髪
        core.rrect(ctx, -20, -152.0 - bob - 6, 40, 44, 14)
        fill(ctx, look["hair"])
        ctx.fill()
    core.rrect(ctx, -19, -134 - bob, 38, 58, 12)       # 体
    fill(ctx, look["shirt"])
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(2.8)
    ctx.stroke()
    for j in (0, 1):                                    # 腕
        sg = -1 if j == 0 else 1
        hand = (sg * 26.0, -76.0 - bob)
        el = (sg * 27.0, -102.0 - bob)
        _limb(ctx, [(sg * 19.0, -127.0 - bob), el, hand], 11.0, look["shirt"])
        fill(ctx, SKIN)
        ctx.arc(hand[0], hand[1], 6.2, 0, 2 * math.pi)
        ctx.fill()
    hy = -152.0 - bob                                   # 頭
    fill(ctx, INK)
    ctx.arc(0, hy, 20.4, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, SKIN)
    ctx.arc(0, hy, 17.6, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, look["hair"])                             # 前髪
    ctx.arc(0, hy - 2, 17.8, math.pi * 1.0, math.pi * 2.0)
    ctx.line_to(11, hy - 6)
    ctx.line_to(-11, hy - 8)
    ctx.close_path()
    ctx.fill()
    fill(ctx, INK)                                      # 目と口
    for ex in (-6.2, 6.2):
        ctx.arc(ex, hy + 1.5, 2.3, 0, 2 * math.pi)
        ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.set_line_width(1.8)
    ctx.arc(0, hy + 7.5, 4.0, math.pi * 0.15, math.pi * 0.85)
    ctx.stroke()
    ctx.restore()


LOOK_P = dict(shirt="#f4ad6a", hair="#3a2f2a", pants="#4a5878", style=1)


def draw_house(ctx, x, yg, w=100.0, h=104.0):
    """家（横から）。x は左端、yg は地面"""
    ctx.save()
    fill(ctx, hexrgb("#ecd9b6"))
    ctx.rectangle(x, yg - h * 0.62, w, h * 0.62)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3)
    ctx.stroke()
    fill(ctx, hexrgb("#c77a63"))
    ctx.move_to(x - 8, yg - h * 0.62)
    ctx.line_to(x + w / 2, yg - h)
    ctx.line_to(x + w + 8, yg - h * 0.62)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.stroke()
    fill(ctx, hexrgb("#fff3c4"))                        # 窓
    ctx.rectangle(x + w * 0.14, yg - h * 0.50, w * 0.26, h * 0.24)
    ctx.fill_preserve()
    ctx.stroke()
    fill(ctx, hexrgb("#8b6b4a"))                        # ドア
    ctx.rectangle(x + w * 0.60, yg - h * 0.42, w * 0.22, h * 0.42)
    ctx.fill_preserve()
    ctx.stroke()
    ctx.restore()


def draw_train(ctx, x, yg, w_car=94.0, h=46.0):
    """電車（横から・2両）。特定の会社に見えない白と灰色。x は左端、yg はレール"""
    ctx.save()
    for i in range(2):
        x0 = x + i * (w_car + 6)
        fill(ctx, hexrgb("#eef0f3"))
        core.rrect(ctx, x0, yg - h - 6, w_car, h, 8)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.95))
        ctx.set_line_width(3)
        ctx.stroke()
        fill(ctx, hexrgb("#8d98ab"))                    # 帯
        ctx.rectangle(x0 + 2, yg - h * 0.47, w_car - 4, 8)
        ctx.fill()
        fill(ctx, hexrgb("#bfe0f5"))                    # 窓
        for k in range(3):
            ctx.rectangle(x0 + 10 + k * w_car * 0.30, yg - h + 3, w_car * 0.22, 16)
            ctx.fill()
        fill(ctx, INK)                                  # 車輪
        for cx in (x0 + 18, x0 + w_car - 18):
            ctx.arc(cx, yg - 4, 6, 0, 2 * math.pi)
            ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))              # レール
    ctx.set_line_width(3)
    ctx.move_to(x - 10, yg + 2)
    ctx.line_to(x + 2 * w_car + 16, yg + 2)
    ctx.stroke()
    ctx.restore()


# ---------- 絵: 温度の色・線 ----------
WARM, COOL, MID = (0.98, 0.72, 0.46), (0.62, 0.78, 0.96), (0.97, 0.94, 0.88)


def temp_color(v):
    """v: −1（冷たい）〜 +1（暖かい）"""
    c = WARM if v > 0 else COOL
    k = min(1.0, abs(v)) * 0.92
    return tuple(MID[i] * (1 - k) + c[i] * k for i in range(3))


_GRAD = {}


def sky_gradient(kind, top):
    key = (kind, round(top))
    if key in _GRAD:
        return _GRAD[key]
    s = sample()
    P = s["q"][kind]
    zmax = SKY_H / ZPX
    zs_ = np.linspace(0, zmax, 24)
    T = np.interp(zs_, P["zk"], P["tk"])
    Tm = T.mean()
    amp = max(0.3, np.abs(T - Tm).max())
    yg = top + SKY_H
    g = cairo.LinearGradient(0, yg, 0, top)
    for z, t_ in zip(zs_, T):
        g.add_color_stop_rgb(z / zmax, *temp_color((t_ - Tm) / amp))
    _GRAD[key] = g
    return g


def ray_xy(zrow, morph_z, top):
    """線 1本の画面の座標（枠の左上を原点にせず、画面の座標で）"""
    d = display()
    n = len(zrow)
    xs = PX0 + X_ORG + np.arange(n) * (X_END - X_ORG) / (n - 1)
    ys = top + SKY_H - morph_z * ZPX
    return xs, ys


def draw_rays(ctx, t, kind, top):
    d = display()
    m = smooth_s((t - T_GO) / BEND)
    flow = (t * 300.0)                                  # 線の上を進む点の動き（px/秒）
    pat = (26.0, 16.0)
    ctx.save()
    ctx.rectangle(PX0, top, PW, SKY_H)
    ctx.clip()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for i in range(len(DISP_TH)):
        z = (1 - m) * d["flat"][i] + m * d[kind][i]
        xs, ys = ray_xy(z, z, top)
        ctx.set_source_rgba(*hexrgb(RAY, 0.22))
        ctx.set_line_width(3.0)
        ctx.set_dash([])
        ctx.move_to(xs[0], ys[0])
        for x_, y_ in zip(xs[1:], ys[1:]):
            ctx.line_to(x_, y_)
        ctx.stroke()
        ctx.set_source_rgba(*hexrgb(RAY, 0.95))
        ctx.set_line_width(9.5)
        ctx.set_dash(list(pat), (pat[0] + pat[1]) - (flow % (pat[0] + pat[1])))
        ctx.move_to(xs[0], ys[0])
        for x_, y_ in zip(xs[1:], ys[1:]):
            ctx.line_to(x_, y_)
        ctx.stroke()
    if kind == "night":                                 # 聞く人のまわりに届いた線（赤）
        a_red = smooth_s((t - T_GO - BEND) / 0.6)
        if a_red > 0:
            for i in range(len(d["red_idx"])):
                z = (1 - m) * d["red_flat"][i] + m * d["red"][i]
                xs, ys = ray_xy(z, z, top)
                ctx.set_source_rgba(*hexrgb(RED, 0.95 * a_red))
                ctx.set_line_width(10.0)
                ctx.set_dash(list(pat), (pat[0] + pat[1]) - (flow % (pat[0] + pat[1])))
                ctx.move_to(xs[0], ys[0])
                for x_, y_ in zip(xs[1:], ys[1:]):
                    ctx.line_to(x_, y_)
                ctx.stroke()
    ctx.set_dash([])
    ctx.restore()


def draw_waves(ctx, t, top, zs):
    """電車から広がる音の波紋（弧）。0秒目から動く"""
    cx, cy = PX0 + X_ORG, top + SKY_H - zs * ZPX
    ctx.save()
    ctx.rectangle(PX0, top, PW, SKY_H)
    ctx.clip()
    for k in range(5):
        ph = ((t * 0.85) + k / 5.0) % 1.0
        r = 20 + 330 * ph
        ctx.set_source_rgba(*hexrgb(RAY, 0.9 - 0.55 * ph))
        ctx.set_line_width(9)
        ctx.arc(cx, cy, r, -1.0, 1.0)
        ctx.stroke()
    ctx.restore()


def hearing(ctx, t, kind, top):
    """聞く人のまわりの様子（届いた数が多いほど大きな弧）"""
    s = sample()
    n = s["n_day"] if kind == "day" else s["n_night"]
    u = smooth_s((t - T_ARR) / CNT_LEN)
    xp, yp = PX0 + X_PERSON, top + SKY_H
    if u <= 0:
        return
    k = 0 if kind == "day" else 1
    if kind == "night":
        for j in range(3):
            ph = ((t * 1.1) + j / 3.0) % 1.0
            r = 22 + 46 * ph
            ctx.set_source_rgba(*hexrgb(RED, 0.9 * (1 - ph) * u))
            ctx.set_line_width(6)
            ctx.arc(xp - 14, yp - 200 + 22, r, math.pi * 0.62, math.pi * 1.38)
            ctx.stroke()
    lab = "よく聞こえる" if kind == "night" else "聞こえにくい"
    b = ease_out((t - T_ARR - 0.5) / 0.3)
    if b > 0:
        w_, h_ = note.sticky(ctx, lab, xp - 120, yp - 236, 38, "yellow" if kind == "night" else "mint", a=b,
                             tilt=-0.03 if kind == "night" else 0.02)


def draw_panel(ctx, t, kind):
    idx = PANEL_IDX[kind]
    top = P_TOPS[idx]
    s = sample()
    yg = top + SKY_H
    ctx.save()
    core.rrect(ctx, PX0, top, PW, PH, 18)
    ctx.clip()
    ctx.set_source(sky_gradient(kind, top))
    ctx.rectangle(PX0, top, PW, SKY_H)
    ctx.fill()
    fill(ctx, hexrgb("#d8c9a2"))                        # 地面
    ctx.rectangle(PX0, yg, PW, PH - SKY_H)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.55))
    ctx.set_line_width(3)
    ctx.move_to(PX0, yg)
    ctx.line_to(PX0 + PW, yg)
    ctx.stroke()
    draw_house(ctx, PX0 + X_HOUSE, yg + 2, 118.0, 124.0)
    draw_train(ctx, PX0 + 16, yg + 4, 114.0, 58.0)
    draw_waves(ctx, t, top, s["zs"])
    draw_rays(ctx, t, kind, top)
    draw_person(ctx, PX0 + X_PERSON, yg + 18, 200.0, LOOK_P)
    hearing(ctx, t, kind, top)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))             # 枠
    ctx.set_line_width(3.5)
    core.rrect(ctx, PX0, top, PW, PH, 18)
    ctx.stroke()
    # 名前の付せんと温度の説明
    note.sticky(ctx, PNAME[kind], PX0 + 78, top + 56, 52, "yellow" if kind == "day" else "blue", tilt=-0.03 if kind == "day" else 0.02)
    fill(ctx, (*hexrgb(PAPER)[:3], 0.80))
    wsub = core.text_width(PSUB[kind], 30) + 26
    core.rrect(ctx, PX0 + 10, top + 118, wsub, 44, 10)
    ctx.fill()
    text(ctx, PSUB[kind], PX0 + 23, top + 140, 30, INK, align="left", bold=False)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    ctx.push_group()
    for kind in ("day", "night"):
        draw_panel(ctx, t, kind)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り（届いた線の数）と、帯の説明 ----------

def fmt(n):
    return f"{int(round(n)):,}"


def draw_readouts(ctx, t):
    if not (T_GO - 0.1 <= t < T_G0):
        return
    a = ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0 + 0.35) / 0.35))
    s = sample()
    if T_GO <= t < T_CAP2:
        text(ctx, "線は 空気の温度で曲がります", 560, 640, 42, INK, alpha=a)
    elif t >= T_CAP2 - 0.2:
        b = ease_out((t - T_CAP2 + 0.2) / 0.3) * a
        text(ctx, "1万本の線のうち、耳のまわりに届いた数", 560, 640, 38, INK, alpha=b)
    if t >= T_ARR - 0.3:
        u = ease_out((t - T_ARR) / CNT_LEN)
        for kind, n in (("day", s["n_day"]), ("night", s["n_night"])):
            top = P_TOPS[PANEL_IDX[kind]]
            xc, yc = PX0 + 700.0, top + 47
            fill(ctx, (*hexrgb(PAPER)[:3], 0.92 * a))
            core.rrect(ctx, PX0 + 420, top + 12, 395, 70, 14)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
            text(ctx, "届いた線", PX0 + 440, yc, 30, INK, align="left", alpha=a)
            col = RED if kind == "night" else INK_D
            text(ctx, fmt(n * u) + "本", PX0 + 798, yc, 52, col, align="right", alpha=a)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 560 - G_COLS * G_CELL / 2, 664.0
_GRID = {}


def categories():
    r = results()
    cat = np.where(r["n_night"] > r["n_day"], np.where(r["n_day"] < 0.5, 0, 1), 2)
    return cat


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    cat = categories()
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra("#3d6fb8"), bgra("#9cc3ee"), bgra(COL_D)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[cat[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_WHY) / 0.35))


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    cat = categories()
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000回（1マス＝1回）", 580, 618, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    cs = cat[:m]
    rows = [("#3d6fb8", "夜が多い（昼はほぼ0本）", int((cs == 0).sum())),
            ("#9cc3ee", "夜が多い（昼にも届いた）", int((cs == 1).sum())),
            (COL_D, "昼が多い・同じ", int((cs == 2).sum()))]
    for i, (col, lab, cnt) in enumerate(rows):
        y = 1190 + i * 50
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(150, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(150, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 204, y, 34, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 34, INK, align="right", alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"やっぱり、{'ABC'[CORRECT]} {NAMES[ORDER[CORRECT]]}が正解。\n"
                         f"夜が多く届いたのは {pct_i(sh['p_night'])}", 580, 1380, 40, "yellow", a=b, tilt=-0.015)


# ---------- なぜ（高校生が一度で分かる言葉で） ----------

def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def arrow(ctx, x0, y0, x1, y1, col, width=8, a=1.0):
    if a <= 0:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()
    ang = math.atan2(y1 - y0, x1 - x0)
    for sg in (-1, 1):
        ctx.move_to(x1, y1)
        ctx.line_to(x1 - 24 * math.cos(ang - sg * 0.5), y1 - 24 * math.sin(ang - sg * 0.5))
        ctx.stroke()


def draw_why_panel(ctx, x0, kind, a, g, t_dir):
    """音の進み方の図。上・真ん中・下の3本の矢印（長さ＝音の速さ）と、その先をつないだ波面。波面に直角な向きに、音は進む"""
    y0, h = 780.0, 340.0
    w = 400.0
    sgn = 1 if kind == "night" else -1                   # 夜は上ほど暖かい（＝速い）、昼は下ほど暖かい
    col = INK_N if kind == "night" else INK_D
    ctx.save()
    core.rrect(ctx, x0, y0, w, h, 14)
    ctx.clip()
    grad = cairo.LinearGradient(0, y0, 0, y0 + h)
    grad.add_color_stop_rgba(0, *temp_color(0.85 * sgn), a)
    grad.add_color_stop_rgba(1, *temp_color(-0.85 * sgn), a)
    ctx.set_source(grad)
    ctx.rectangle(x0, y0, w, h)
    ctx.fill()
    xs = x0 + 55
    ys = (y0 + 55, y0 + h / 2, y0 + h - 55)
    lens = (235.0, 180.0, 125.0) if sgn > 0 else (125.0, 180.0, 235.0)
    tips = []
    for y, ln in zip(ys, lens):
        L = ln * g
        arrow(ctx, xs, y, xs + L, y, col, 9, a)
        tips.append((xs + L, y))
    ctx.set_source_rgba(*hexrgb(INK, 0.5 * a))           # さいしょの波面
    ctx.set_line_width(5)
    ctx.set_dash([10, 8])
    ctx.move_to(xs, ys[0] - 20)
    ctx.line_to(xs, ys[2] + 20)
    ctx.stroke()
    ctx.set_dash([])
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))           # いまの波面
    ctx.set_line_width(7)
    ctx.move_to(tips[0][0], tips[0][1] - 14 * g)
    ctx.line_to(tips[2][0], tips[2][1] + 14 * g)
    ctx.stroke()
    td = ease_out(t_dir)
    if td > 0:                                           # 波面に直角に、音の進む向き
        dx_, dy_ = tips[2][0] - tips[0][0], tips[2][1] - tips[0][1]
        nx, ny = dy_, -dx_
        if nx < 0:
            nx, ny = -nx, -ny
        nl = math.hypot(nx, ny)
        nx, ny = nx / nl, ny / nl
        mx_, my_ = tips[1]
        arrow(ctx, mx_, my_, mx_ + nx * 105 * td, my_ + ny * 105 * td, RED, 11, a)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(3.5)
    core.rrect(ctx, x0, y0, w, h, 14)
    ctx.stroke()
    ys_lab = (("速い", "遅い") if sgn > 0 else ("遅い", "速い"))
    if g > 0.6:
        b = clamp01((g - 0.6) / 0.4) * a
        text(ctx, ys_lab[0], tips[0][0] + 16, ys[0] - 24, 30, INK, align="left", alpha=b)
        text(ctx, ys_lab[1], tips[2][0] + 16, ys[2] + 24, 30, INK, align="left", alpha=b)
    text(ctx, "夜" if kind == "night" else "昼", x0 + 30, y0 - 30, 44, col, align="left", alpha=a)
    text(ctx, "上ほど暖かい" if kind == "night" else "上ほど冷たい", x0 + 100, y0 - 28, 30, INK, align="left", bold=False, alpha=a)


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    text(ctx, "音は 暖かい空気ほど 速く進む", 560, 636, 42, INK, alpha=a)
    text(ctx, "気温が1℃上がると、音は毎秒0.6mほど速くなる", 560, 690, 28, INK, bold=False, alpha=a)
    g = ease_out((t - T_WHY - 0.6) / 1.2)
    t_dir = (t - T_WHY - 2.0) / 0.5
    draw_why_panel(ctx, 95.0, "night", a, g, t_dir)
    draw_why_panel(ctx, 560.0, "day", a, g, t_dir)
    t1 = T_WHY + 2.4
    if t >= t1:
        b = ease_out((t - t1) / 0.3) * a
        note.sticky(ctx, "夜は 音が\n地面のほうへ\n曲がって届く", 300, 1270, 36, "blue", a=b, tilt=-0.015)
    t2 = T_WHY + 4.0
    if t >= t2:
        b = ease_out((t - t2) / 0.3) * a
        note.sticky(ctx, "昼は 音が\n上へ逃げて\nほとんど届かない", 760, 1270, 36, "yellow", a=b, tilt=0.015)
    t3 = T_WHY + 4.4
    if t >= t3:
        b = ease_out((t - t3) / 0.3) * a
        text(ctx, "この置き方なら、昼はほとんど届きません", 520, 1384, 32, INK, bold=False, alpha=b)
        text(ctx, "実際は昼も、空気のゆれなどで少しは届きます", 520, 1424, 32, RED, bold=False, alpha=b)


# ---------- ひねり: 空気がぜんぶ同じ温度なら？ ----------

def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + 3 * 0.5 + 0.5


def bars(ctx, t, t0, rows, ys, a, x0, ln, vmax, step=0.5, hh=34, lab=40, val=44, lab_dy=64):
    for i, ((lab_s, v_, col, val_s), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * step
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab_s, x0, y - lab_dy, lab, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - hh, ln, 2 * hh)
        ctx.stroke()
        w = ln * min(1.0, v_ / vmax) * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - hh, w, 2 * hh, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, val_s, x0 + ln + 16, y, val, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "届いた本数の真ん中（1万回）", 560, 640, 42, INK, alpha=a)
    vmax = max(sh["nn_med"], 1.0) * 1.0
    rows = [("音が曲がらないとき", sh["nf_med"], "#c9c4b4", f"約{fmt(sh['nf_med'])}本"),
            ("昼", sh["nd_med"], COL_D, f"約{fmt(sh['nd_med'])}本"),
            ("夜", sh["nn_med"], COL_N, f"約{fmt(sh['nn_med'])}本")]
    bars(ctx, t, T_TW_RUN, rows, (850.0, 1020.0, 1190.0), a, x0=150.0, ln=520.0, vmax=vmax * 1.0)
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        k = sh["nn_med"] / sh["nf_med"]
        note.sticky(ctx, "音が曲がらないときより、\n夜は 多く届く。\n昼は ほとんど届かない", 570, 1350, 40, "pink", fg=RED, a=b, tilt=-0.02)


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


CD_X, CD_Y = 190.0, 1385.0
Q_CX = 560.0                                      # 問いの中心（x 120〜1000 に収める）
Q_W = 856.0                                       # 問いの幅（この幅いっぱいに大きく）


class YIntro(note.Intro):
    """この回だけの冒頭。上: 大きな問い2行（同じ大きさ）・前提・三択（横1列）。その下いっぱいに、昼と夜の場面（0秒目から音の線が動いている）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        w = max(core.text_width(l, 100) for l in BIG_Q)
        sz = 100.0 * Q_W / w
        pop = 1 + 0.025 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (440, 440 + sz * 1.12)):
            ctx.save()
            ctx.translate(Q_CX, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        yl = 440 + sz * 1.12 + sz * 0.56
        note.pen_line(ctx, Q_CX - w2 / 2 - 6, yl + 4, Q_CX + w2 / 2 + 6, yl - 2, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        yd = yl + 44
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 560, yd, 34, INK, bold=False, alpha=a1)
        yc = yd + 54
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 560, 820)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, yc, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, yc, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, yc, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.94 * a2))
            core.rrect(ctx, cx - 125, cy - 150, 250, 220, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 150, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 98, 40, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 54, 52, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 74, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        w = max(core.text_width(l, 100) for l in BIG_Q)
        sz = min(56.0, 100.0 * 800.0 / w)
        text(ctx, BIG_Q[0], 540, 406, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 406 + sz * 1.13, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        yl = 406 + sz * 1.13 + sz * 0.56
        note.pen_line(ctx, 540 - w2 / 2 - 6, yl + 3, 540 + w2 / 2 + 6, yl, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = yl + 50
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840)):
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


INTRO = YIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 時間割（動画の秒）の続き ----------
T_G0 = T_GO + RACE_LEN                            # 1万回のマス目
T_G1 = T_G0 + 2.4
T_REV = T_G1 + 0.8                                # 答え
T_WHY = T_REV + 3.8                               # なぜ
T_TW = T_WHY + 7.8                                # ひねり
T_TW_RUN = T_TW + 3.8
T_Q = T_TW_RUN + 5.6                              # 締め
DURATION = T_Q + 4.6


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.2:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 0.8) / 0.4))
        note.sticky(ctx, "スタート", 300, 1140, 40, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、音が曲がらなかったら？\n（気温がどこも同じなら）", 560, 980, a=ba, t_rel=t - T_TW, size=46)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたの家からは、\n夜に何の音が\n聞こえますか？", 570, 1000, 64, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 570, 1330, 44, INK, bold=False, alpha=r)


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
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for k in range(int(T_GO / 0.85) + 1):             # 音の波紋に合わせた、うすいピッ
        if k * 0.85 < T_GO - 0.8:
            mx.add(k * 0.85 + 0.05, tick(1760.0, 0.04), 0.07)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    mx.add(T_GO + 0.2, whoosh(BEND), 0.25)
    beat(mx, T_GO + 0.5, T_ARR - 0.2, bpm=124, vol=0.30)
    for j in range(4):
        mx.add(T_ARR + j * 0.45, blip(880.0 + 110 * j, 0.1), 0.25)
    mx.add(T_ARR + 1.9, bell(784.0, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(2):                                 # なぜ
        mx.add(T_WHY + 0.9 + i * 0.5, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(3):
        mx.add(T_TW_RUN + 0.3 + i * 0.5, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    checks = []
    # (1) 音の速さの式: 0℃で331.5、20℃で343.5（教科書の約343 m/秒）
    checks.append(("音の速さ 20℃（m/秒）", float(c_of_T(20.0)), 343.4, 0.2))
    # (2) 閉じた式で数えた届いた線 と、1歩ずつ進めて（0.25 m刻み）数えた線 が一致するか。12回 × 昼・夜・曲がらない
    th = THETA[::10]
    worst_agree, worst_rel, rels = 1.0, 0.0, []
    for i in range(12):
        q = trial_params(5, i)
        for kind in ("day", "night", "flat"):
            ov = box_overlap(q[kind], q["zs"], q["R"], th)
            fl = trace_flags(q[kind], q["zs"], q["R"], th, 0.25)
            worst_agree = min(worst_agree, float(np.mean((ov > 0) == fl)))
            zz = trace(q[kind], q["zs"], th, q["R"] + BOX_W + 0.25, 0.25)
            xs = np.arange(zz.shape[1]) * 0.25
            m = (xs >= q["R"] - BOX_W) & (xs <= q["R"] + BOX_W)
            n_br = (zz[:, m] <= BOX_H).sum() * 0.25 / (2 * BOX_W) * 10      # 線を10本おきに間引いたので10倍
            n_an = ov.sum() / (2 * BOX_W) * 10
            if max(n_br, n_an) > 20:
                rels.append(abs(n_an - n_br) / max(n_br, n_an))
                worst_rel = max(worst_rel, rels[-1])
    checks.append(("閉じた式と1歩ずつの計算で 届く線かどうかが一致する割合（最小）", worst_agree, 1.0, 0.03))
    # 線ごとの位置は、何度も折り返すうちに数mずれる（歩幅0.25mの誤差が積もる）ので、本数の合計で比べる
    checks.append(("同じく 届いた本数の違い（割合・平均）", float(np.mean(rels)), 0.0, 0.03))
    checks.append(("同じく 届いた本数の違い（割合・最大）", worst_rel, 0.0, 0.08))
    # (3) 音が曲がらない空気: 本数 ＝ 6 /（距離 × 線の間隔）（まっすぐな線は 直接＋地面ではね返った線の2通りで、箱の高さ3m）
    dth = 2 * TH_MAX / (N_RAY - 1)
    worst = 0.0
    for i in range(20):
        q = trial_params(11, i)
        n = count_rays(q["flat"], q["zs"], q["R"])
        worst = max(worst, abs(n - 6 * BOX_H / 3 / (q["R"] * dth)) / (6 / (q["R"] * dth)))
    checks.append(("音が曲がらない空気の本数と式 6/(R×間隔) の違い（割合・最大）", worst, 0.0, 0.01))
    # (4) 箱の中で何度も往復する線の近似（8回まで足して、それ以上は割合で近似）が、40回まで足した値とほぼ同じ
    global J_LOOP
    worst = 0.0
    for i in range(30):
        q = trial_params(13, i)
        J_LOOP = 8
        a = count_rays(q["night"], q["zs"], q["R"])
        J_LOOP = 40
        b = count_rays(q["night"], q["zs"], q["R"])
        worst = max(worst, abs(a - b) / b)
    J_LOOP = 8
    checks.append(("往復の近似（8回 → 40回）の違い（割合・最大）", worst, 0.0, 0.03))
    # (5) 同じ種で作り直すと同じ値（キャッシュと一致）
    for i in (0, 1, 2, 3, 4):
        t_ = trial(SEED_MAIN, i)
        checks.append((f"{i}回目の再計算（昼・夜の本数）", t_[2] + t_[3], float(r["n_day"][i] + r["n_night"][i]), 1e-6))
    # (6) 回数の合計
    checks.append(("夜が多い・昼が多い・同じ の合計", float(sh["n_night_more"] + sh["n_day_more"] + sh["n_tie"]), float(N_TRIAL), 0.0))
    # (7) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(ORDER[INTRO.correct]), float(answer_by_rule(sh["p_night"], sh["r_med"])), 0.0))
    # (8) 見本: 1万回の中の1回。赤で描く線は 箱を通る線（1歩ずつ進めて確かめる）
    s = sample()
    d = display()
    fl = trace_flags(s["q"]["night"], s["zs"], s["R"], THETA[d["red_idx"]], 0.2)
    checks.append(check_true("赤で描く3本が、1歩ずつの計算でも箱を通る", bool(fl.all() and len(fl) == 3), ""))
    checks.append(check_true("見本の昼は、ほぼ届かない（0.5本未満）", s["n_day"] < 0.5, f"{s['n_day']:.2f}本"))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    s = sample()
    q = s["q"]
    print(f"長さ {DURATION:.1f}秒  曲がる {T_GO:.1f}  届く {T_ARR:.1f}  マス目 {T_G0:.1f}  答え {T_REV:.1f}  なぜ {T_WHY:.1f}  ひねり {T_TW:.1f}  締め {T_Q:.1f}"
          f"  見本 {s['i']}（{s['R']:.0f}m  昼 {s['n_day']:.1f} / 夜 {s['n_night']:.0f} / 曲がらない {s['n_flat']:.0f}本）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.0, 5.0, 8.0, 8.6, 9.5, 11.0, 13.0, 15.5, T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 3.0,
              T_WHY + 5.5, T_TW + 1.0, T_TW_RUN + 3.5, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
