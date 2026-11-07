"""加湿器は、床に置く？ 高い所に置く？ 同じ部屋2つ（床／高さ1m前後の棚の上）で、暖房した部屋に1時間。1万回。— 2026-10-27 作成（公開予定 11/07・45秒前後）

くらべるのは「部屋の真ん中の、座った顔の高さの湿度が、1時間でどれだけ上がるか」だけ。
（体のこと・お金・電気代・機種名は入れない。画面にも概要欄にも書かない）

モデル（部屋の空気を高さ方向に 8 層 = 0.3 m ずつ。水平方向は一様＝仮定。1時間を 6 秒きざみで進める）
  各層の水蒸気量 ρ_i [g/m³]。1層ごとに、次のものを足し引きする:
    ① 加湿器が出す水蒸気   … 出す量 m [g/h] を、吹き出し口の高さ z_s から 上へ h_rise の範囲の層に 均等に配る（吹き出しの勢い＋暖かく湿った空気の浮力ぶん上へ）
         m = 定格 × 0.7〜1.0（定格は部屋の面積 × 21〜36 mL/h/m² を 200〜750 に収めた値）   … 定格の幅: 200〜750 mL/h は市販3機種
              https://panasonic.jp/kashitsu/p-db/FE-KFU03_spec.html https://jp.sharp/kashitsu/products/hvt75/spec/ （1畳あたり 35〜60 mL/h → 1 m² あたり 21〜36）
              定格は JEM1426（日本電機工業会）の「室温20℃・湿度30%」の値で、湿度が高いほど・室温が低いほど減る（同じ資料）→ 0.7〜1.0 を掛けた（仮定）
         z_s: 床置き 0.25〜0.40 m / 棚の上（棚の高さ 0.8〜1.2 m ＋ 本体 0.3 m）1.1〜1.5 m   … 仮定（床から30〜60cm・卓上70〜100cm という民間記事 https://lifestyle.assist-all.co.jp/humidifier-placement-livingroom-best-way-tips-safety/ は根拠不明なので使っていない）
         h_rise = 0.2〜1.2 m   … 仮定（吹き出しの勢い・浮力の測定値は確認できなかった）
    ② 暖房の空気の流れと層のあいだの混ざり   … 層のあいだの渦拡散 K = 0.002〜0.05 m²/s（対数一様）。部屋ぜんたいが混ざる時間 L²/K ≒ 2〜50 分   … 仮定
         暖房の向き（下向き／水平／上向き）で、その高さの層のあいだだけ K が 1〜4 倍（下向き: 1.2 m より下 / 水平: 1.2〜1.8 m / 上向き: 1.8 m より上）   … 仮定
    ③ 換気   … 0.5〜2.0 回/h（すきま風を含む・仮定。基準は 0.5 回/h＝1時間に部屋の空気の半分が入れ替わる。国土交通省 https://www.mlit.go.jp/jutakukentiku/build/jutakukentiku_house_fr_000108.html ）
         外気: -2〜10℃・湿度 40〜70%   … 仮定
    ④ 壁・家具・布の水蒸気の吸いこみ   … 層ごとに「ため池」（空気の β 倍まで、時定数 τ で空気の湿度に近づく）。β = 0.5〜3、τ = 10〜30 分   … 仮定（出典なし。実際に吸う量は材料しだい＝加湿量の一部が壁などに消える、という FACTCHECK の説明のみ）
    ⑤ 結露（水が空気から減る）
         床: 床の表面温度 11〜20℃（かつ 床近くの空気より 0.5℃以上低い）より ρ_床の層 が飽和量より大きければ、その超えた分が h_m で床に着く   … 床の表面温度の出典なし＝仮定
              （断熱の悪い床 10〜15℃・断熱された床 16〜20℃ の物理的な見当。FACTCHECK 3-2「確認できない」）
         窓: 高さ 0.9〜2.1 m・幅 1.0〜3.0 m、ガラス内側の温度 Tg = T層 − (T層 − T外) × U / α（U = 5.8 単板 または 2.9 複層、α = 8.7）… 式と α は北海道立総合研究機構 https://www.hro.or.jp/upload/50471/1041204.pdf 、U は 中小機構 https://j-net21.smrj.go.jp/development/energyeff/Q1225.html
         着く量 = h_m × (ρ − ρ_sat(T表面)) × 面積。h_m = h_c ÷ (ρ_空気 c_p Le^(2/3))、h_c = 2.5〜4.0 W/m²K・Le = 0.85〜0.90   … 仮定（kaaten-ketsuro と同じ）
         空気が飽和（湿度 100%）を超えたら、超えた分は霧になって落ちる（湿度が 100% を超えない）
    飽和水蒸気量 ρ_sat = 216.7 × e_s ÷ (T + 273.15) [g/m³]、e_s = 6.112 × exp(17.62 T/(243.12+T)) [hPa]（Magnus の式・WMO）
  暖房した部屋の上下の温度: 顔の高さ（約 1.05 m）の室温 18〜23℃。床付近と 1.1 m の差 ΔT = 1〜6 K（実測例 5℃（床22℃・床上110cm 27℃）、基準は 3〜4K 以内が望ましい）
         https://www.sumaken-lab.com/wellness-note/210123/ 、 https://en.wikipedia.org/wiki/ASHRAE_55
         上へは 同じ傾きでまっすぐ（天井の値は確認できなかった＝仮定）
  部屋: 面積 8〜20 m²（5〜12畳）、天井高 2.4 m、はじめの湿度（顔の高さ）30〜50%（はじめは部屋じゅう同じ水蒸気量）
  人・湿度計: 座った顔の高さ 1.0〜1.2 m の層（3番目の層 0.9〜1.2 m）の 相対湿度（その層の温度で）を読む。
  入れていないもの: 水平方向のちがい（加湿器の目の前は濃く、遠くは薄い）、霧の粒の蒸発、加湿器のセンサーが湿度を高めに判定して出す量を落とす説（メディア記事のみで公的な裏付けなし）、
      加湿で室温が下がる分、人の呼吸、窓以外の壁の結露、天井の温度。
  だから答えは計算どおり。「ほぼ同じ」「床」になってもそのまま出す。

問い: 「加湿器、/ 床に置く？/ 高い所に置く？」＋「部屋の真ん中の湿度が早く上がるのは？」
      選択肢（記号の並びは LABELS の順。正解の記号は A になるように並べる）: 床 ／ ほぼ同じ ／ 高い所
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1時間で 部屋の真ん中（座った顔の高さ）の湿度が より上がった回の割合 p（高い所のほうが上がった割合）と、
      上がり方の差（高い所 − 床・ポイント）の中央値 g で、
      p ≥ 60% かつ g ≥ 3ポイント なら「高い所」、p ≤ 40% かつ g ≤ -3ポイント なら「床」、それ以外は「ほぼ同じ」。
ひねり: 1行だけ。「では、エアコンの風が当たる所に置いたら？」（K を 3〜10 倍にして同じ1万回を再計算）。
締め: 「あなたの家の加湿器、どこに置いていますか？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（並んで上がっていく2つの部屋）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "kashitsuki-basho"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261107
NL, ROOM_H = 8, 2.4                                # 層の数・天井高（m）
DZ = ROOM_H / NL
ZC = (np.arange(NL) + 0.5) * DZ                    # 層の中心の高さ
FACE_L = 3                                         # 座った顔の高さの層（0.9〜1.2 m）
Z_FACE = 1.05
HOUR = 3600.0
DT_S = 6.0
T_FACE, DT_FLOOR = (18.0, 23.0), (1.0, 6.0)        # 顔の高さの室温、床付近と 1.1 m の温度差（K）
RH0 = (0.30, 0.50)
AREA = (8.0, 20.0)
RATED_PER_M2, RATED_CLIP = (21.0, 36.0), (200.0, 750.0)
OUT_FRAC = (0.7, 1.0)
ZS_FLOOR, SHELF_TOP, BODY_H = (0.25, 0.40), (0.8, 1.2), 0.3
H_RISE = (0.2, 1.2)
K_LOG = (0.002, 0.05)
K_BOOST = (1.0, 4.0)
K_TWIST = (3.0, 10.0)                              # ひねり: エアコンの風が当たる所 → K がこの倍
ACH = (0.5, 2.0)
T_OUT, RH_OUT = (-2.0, 10.0), (0.40, 0.70)
BETA, TAU_B = (0.5, 3.0), (600.0, 1800.0)
T_FS = (11.0, 20.0)                                # 床の表面温度
WIN_W, WIN_Z = (1.0, 3.0), (0.9, 2.1)
U_WIN = (5.8, 2.9)
ALPHA_I = 8.7
HC_IN, LEWIS = (2.5, 4.0), (0.85, 0.90)
RHO_AIR, CP_AIR = 1.2, 1006.0

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_P_HI, RULE_P_LO, RULE_G_HI, RULE_G_LO = 0.60, 0.40, 3.0, -3.0


def answer_by_rule(p_high, g_med):
    """p_high = 高い所のほうが顔の高さの湿度が上がった割合、g_med = 上がり方の差（高い所 − 床・ポイント）の中央値。'high' / 'same' / 'floor'"""
    if p_high >= RULE_P_HI and g_med >= RULE_G_HI:
        return "high"
    if p_high <= RULE_P_LO and g_med <= RULE_G_LO:
        return "floor"
    return "same"


def es_hpa(T):
    return 6.112 * np.exp(17.62 * T / (243.12 + T))


def rho_sat(T):
    """飽和水蒸気量 g/m³"""
    return 216.7 * es_hpa(T) / (np.asarray(T, float) + 273.15)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    A = u(AREA)
    rated = np.clip(A * u(RATED_PER_M2), RATED_CLIP[0], RATED_CLIP[1])
    d = dict(Tf=u(T_FACE), dT=u(DT_FLOOR), rh0=u(RH0), A=A, rated=rated, outf=u(OUT_FRAC),
             zs_f=u(ZS_FLOOR), zs_h=u(SHELF_TOP) + BODY_H, hr=u(H_RISE),
             K0=np.exp(rng.uniform(math.log(K_LOG[0]), math.log(K_LOG[1]), n)), dirn=rng.integers(0, 3, n), boost=u(K_BOOST),
             ach=u(ACH), To=u(T_OUT), rho=u(RH_OUT), beta=u(BETA), tau=u(TAU_B),
             tfs=u(T_FS), ww=u(WIN_W), U=np.where(rng.random(n) < 0.5, U_WIN[0], U_WIN[1]),
             hc=u(HC_IN), Le=u(LEWIS), qk=u(K_TWIST))
    d["m"] = d["rated"] * d["outf"]                # 出す量 g/h（1 mL = 1 g）
    return d


def temp_profile(d):
    """各層の室温 (n, NL)。顔の高さの室温を基準に、1.1 m までの差 dT の傾きで まっすぐ"""
    g = d["dT"] / 1.1
    return d["Tf"][:, None] + g[:, None] * (ZC[None, :] - Z_FACE)


def interface_K(d, twist=False):
    """層のあいだ (NL-1 か所) の渦拡散係数 (n, NL-1)"""
    zi = DZ * np.arange(1, NL)
    K = np.repeat(d["K0"][:, None], NL - 1, axis=1)
    b = (d["boost"] - 1.0)[:, None]
    lo, mid, hi = (zi < 1.2)[None, :], ((zi >= 1.2) & (zi <= 1.8))[None, :], (zi > 1.8)[None, :]
    dn = d["dirn"][:, None]
    K = K * (1.0 + b * (((dn == 0) & lo) | ((dn == 1) & mid) | ((dn == 2) & hi)))
    if twist:
        K = K * d["qk"][:, None]
    return K


def source_weights(zs, hr):
    """吹き出し口の高さ zs から 上へ hr の範囲に 均等に（層ごとの重なりで）配る (n, NL)"""
    lo = np.arange(NL) * DZ
    hi = lo + DZ
    a = zs[:, None]
    b = np.minimum(zs + hr, ROOM_H)[:, None]
    ov = np.clip(np.minimum(hi[None, :], b) - np.maximum(lo[None, :], a), 0.0, None)
    s = ov.sum(axis=1, keepdims=True)
    return ov / np.maximum(s, 1e-12)


def tri_factor(r):
    """(I - 拡散) の LU（トーマス法）。r = dt K / dz² (n, NL-1)"""
    n = r.shape[0]
    lo = np.zeros((n, NL))
    up = np.zeros((n, NL))
    dg = np.ones((n, NL))
    dg[:, :-1] += r
    dg[:, 1:] += r
    lo[:, 1:] = -r
    up[:, :-1] = -r
    den = np.zeros((n, NL))
    cp = np.zeros((n, NL))
    den[:, 0] = dg[:, 0]
    cp[:, 0] = up[:, 0] / den[:, 0]
    for i in range(1, NL):
        den[:, i] = dg[:, i] - lo[:, i] * cp[:, i - 1]
        cp[:, i] = up[:, i] / den[:, i]
    return lo, den, cp


def tri_solve(fac, b):
    lo, den, cp = fac
    dp = np.zeros_like(b)
    dp[:, 0] = b[:, 0] / den[:, 0]
    for i in range(1, NL):
        dp[:, i] = (b[:, i] - lo[:, i] * dp[:, i - 1]) / den[:, i]
    x = np.zeros_like(b)
    x[:, -1] = dp[:, -1]
    for i in range(NL - 2, -1, -1):
        x[:, i] = dp[:, i] - cp[:, i] * x[:, i + 1]
    return x


def simulate(d, where="floor", twist=False, rec_every=0):
    """1時間。where = 'floor' / 'high'。返り値 dict: rh_face0, rh_face1（顔の高さの相対湿度 0〜1）、損失の内訳（g）、rec（rec_every 秒ごとの各層の ρ と 顔の湿度、量）"""
    n = len(d["m"])
    T = temp_profile(d)
    rs = rho_sat(T)
    rho = (d["rh0"] * rho_sat(d["Tf"]))[:, None] * np.ones((1, NL))          # はじめは部屋じゅう同じ水蒸気量
    rhb = rho / rs                                                             # ため池の湿度は空気と平衡
    zs = d["zs_f"] if where == "floor" else d["zs_h"]
    w = source_weights(zs, d["hr"])
    vol = d["A"] * DZ                                                          # 1層の体積
    S = d["m"] / HOUR                                                          # g/s
    K = interface_K(d, twist)
    fac = tri_factor(DT_S * K / DZ ** 2)
    rho_out = (d["rho"] * rho_sat(d["To"]))[:, None]
    hm = d["hc"] / (RHO_AIR * CP_AIR * d["Le"] ** (2.0 / 3.0))
    # 床
    T_a0 = T[:, 0]
    tfs = np.minimum(d["tfs"], T_a0 - 0.5)
    rs_fs = rho_sat(tfs)
    # 窓
    z0, z1 = WIN_Z[0], WIN_Z[1]
    lo_l, hi_l = np.arange(NL) * DZ, np.arange(NL) * DZ + DZ
    f_win = np.clip(np.minimum(hi_l, z1) - np.maximum(lo_l, z0), 0.0, DZ) / DZ                # 層ごとの窓の割合（共通）
    Tg = T - (T - d["To"][:, None]) * d["U"][:, None] / ALPHA_I
    rs_g = rho_sat(Tg)
    k_win = (hm * d["ww"] / d["A"])[:, None] * f_win[None, :] * DT_S
    k_floor = np.minimum(hm / DZ * DT_S, 1.0)
    f_buf = DT_S / d["tau"]
    steps = int(HOUR / DT_S)
    inj = vent = buf = fl = wn = fog = 0.0 * d["m"]
    rec = []
    rh_face0 = rho[:, FACE_L] / rs[:, FACE_L]
    for s in range(steps):
        if rec_every and s % int(rec_every / DT_S) == 0:
            rec.append((s * DT_S, rho.copy(), (rho[:, FACE_L] / rs[:, FACE_L]).copy(), fl.copy() if np.ndim(fl) else fl, wn.copy() if np.ndim(wn) else wn))
        add = S[:, None] * w * DT_S / vol[:, None]
        rho = rho + add
        inj = inj + S * DT_S
        dv = d["ach"][:, None] / HOUR * DT_S * (rho_out - rho)
        rho = rho + dv
        vent = vent + (-dv * vol[:, None]).sum(axis=1)                         # 部屋から出ていった量（外から入る分は負）
        ex = f_buf[:, None] * (rho - rhb * rs)
        rho = rho - ex
        rhb = rhb + ex / (d["beta"][:, None] * rs)
        buf = buf + (ex * vol[:, None]).sum(axis=1)
        e0 = np.maximum(rho[:, 0] - rs_fs, 0.0) * k_floor
        rho[:, 0] -= e0
        fl = fl + e0 * vol
        ew = np.maximum(rho - rs_g, 0.0) * np.minimum(k_win, 1.0)
        rho = rho - ew
        wn = wn + (ew * vol[:, None]).sum(axis=1)
        rho = tri_solve(fac, rho)
        ef = np.maximum(rho - rs, 0.0)                                          # 100% を超えたら 霧になって落ちる（混ざったあとに確かめる）
        rho = rho - ef
        fog = fog + (ef * vol[:, None]).sum(axis=1)
    rec.append((steps * DT_S, rho.copy(), (rho[:, FACE_L] / rs[:, FACE_L]).copy(), fl.copy() if np.ndim(fl) else fl, wn.copy() if np.ndim(wn) else wn))
    return dict(rh0=rh_face0, rh1=rho[:, FACE_L] / rs[:, FACE_L], inj=inj, vent=vent, buf=buf, floor=fl, win=wn, fog=fog,
                rho=rho, rs=rs, rec=rec, rs_fs=rs_fs, tfs=tfs)
# ---- MODEL END ----

_RES = {}


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


def results():
    if _RES:
        return _RES["m"]
    d = draw_params(np.random.default_rng(SEED_MAIN), N_TRIAL)
    f = simulate(d, "floor")
    h = simulate(d, "high")
    ft = simulate(d, "floor", twist=True)
    ht = simulate(d, "high", twist=True)
    pt = lambda x: 100.0 * (x["rh1"] - x["rh0"])                       # 上がり方（ポイント）    # noqa: E731
    r = dict(p=d, f=f, h=h, ft=ft, ht=ht, up_f=pt(f), up_h=pt(h), up_ft=pt(ft), up_ht=pt(ht))
    _RES["m"] = r
    return r


def stats(up_f, up_h):
    diff = up_h - up_f
    return dict(p=float((diff > 0).mean()), g=float(np.median(diff)), n_hi=int((diff > 0).sum()), n_fl=int((diff < 0).sum()),
                n_eq=int((diff == 0).sum()), diff=diff, mf=float(np.median(up_f)), mh=float(np.median(up_h)))


def shown():
    r = results()
    s1 = stats(r["up_f"], r["up_h"])
    s2 = stats(r["up_ft"], r["up_ht"])
    p = r["p"]
    lost = lambda x: (x["floor"] + x["win"] + x["fog"]) / x["inj"]            # noqa: E731
    out = dict(s1=s1, s2=s2, lost_f=float(np.median(lost(r["f"]))), lost_h=float(np.median(lost(r["h"]))),
               floor_f=float(np.median(r["f"]["floor"] / r["f"]["inj"])), floor_h=float(np.median(r["h"]["floor"] / r["h"]["inj"])),
               p_floor_wet_f=float((r["f"]["floor"] > 1e-9).mean()), p_floor_wet_h=float((r["h"]["floor"] > 1e-9).mean()),
               win_f=float(np.median(r["f"]["win"] / r["f"]["inj"])), win_h=float(np.median(r["h"]["win"] / r["h"]["inj"])),
               fog_f=float((r["f"]["fog"] > 1e-9).mean()), fog_h=float((r["h"]["fog"] > 1e-9).mean()),
               rh_max=float(max(r["f"]["rh1"].max(), r["h"]["rh1"].max(), r["ft"]["rh1"].max(), r["ht"]["rh1"].max())),
               up_med=(float(np.median(r["up_f"])), float(np.median(r["up_h"]))), up_pct=np.percentile(np.concatenate([r["up_f"], r["up_h"]]), [5, 50, 95]),
               buf_f=float(np.median(r["f"]["buf"] / r["f"]["inj"])), vent_f=float(np.median(r["f"]["vent"] / r["f"]["inj"])))
    # 感度: K の小さい半分・大きい半分
    kh = p["K0"] > np.median(p["K0"])
    out["s_klo"] = stats(r["up_f"][~kh], r["up_h"][~kh])
    out["s_khi"] = stats(r["up_f"][kh], r["up_h"][kh])
    hh = p["hr"] > np.median(p["hr"])
    out["s_hlo"] = stats(r["up_f"][~hh], r["up_h"][~hh])
    out["s_hhi"] = stats(r["up_f"][hh], r["up_h"][hh])
    spread = lambda x: float(np.median((x["rho"].max(axis=1) - x["rho"].min(axis=1)) / x["rho"].mean(axis=1)))   # noqa: E731
    out["spread_f"], out["spread_h"] = spread(r["f"]), spread(r["h"])
    out["spread_ft"], out["spread_ht"] = spread(r["ft"]), spread(r["ht"])
    return out


def report():
    sh = shown()
    s1, s2 = sh["s1"], sh["s2"]
    print(f"p（高い所のほうが上がった）= {s1['p']:.4f}  g（高い所 − 床・中央値）= {s1['g']:+.2f} ポイント  → 答え {answer_by_rule(s1['p'], s1['g'])}")
    print(f"  高い所が上 {s1['n_hi']}回 / 床が上 {s1['n_fl']}回 / 同じ {s1['n_eq']}回   1時間の上がり方の中央値 床 {s1['mf']:.1f} / 高い所 {s1['mh']:.1f} ポイント"
          f"（全体の 5/50/95% = {np.round(sh['up_pct'], 1)}）")
    print(f"  ひねり（エアコンの風）: p = {s2['p']:.4f}  g = {s2['g']:+.2f}  → {answer_by_rule(s2['p'], s2['g'])}   上がり方の中央値 床 {s2['mf']:.1f} / 高い所 {s2['mh']:.1f}")
    print(f"  顔の高さの湿度の最大（全シナリオ）{sh['rh_max'] * 100:.1f}%")
    print(f"  [内訳 中央値・加湿量に対する割合] 結露＋霧で消えた量 床 {sh['lost_f']:.3f} / 高い所 {sh['lost_h']:.3f}   床に着いた 床 {sh['floor_f']:.4f} / 高い所 {sh['floor_h']:.4f}"
          f"（床に結露した回 {sh['p_floor_wet_f']:.3f} / {sh['p_floor_wet_h']:.3f}）  窓 {sh['win_f']:.3f} / {sh['win_h']:.3f}  霧になった回 {sh['fog_f']:.3f} / {sh['fog_h']:.3f}")
    print(f"  [感度] 混ざりが弱い半分（K小）: p = {sh['s_klo']['p']:.3f} g = {sh['s_klo']['g']:+.2f} → {answer_by_rule(sh['s_klo']['p'], sh['s_klo']['g'])}"
          f" / 強い半分（K大）: p = {sh['s_khi']['p']:.3f} g = {sh['s_khi']['g']:+.2f} → {answer_by_rule(sh['s_khi']['p'], sh['s_khi']['g'])}")
    print(f"  [感度] 吹き出しが上へ届きにくい半分: p = {sh['s_hlo']['p']:.3f} g = {sh['s_hlo']['g']:+.2f} / 届く半分: p = {sh['s_hhi']['p']:.3f} g = {sh['s_hhi']['g']:+.2f}")
    print(f"  [1時間後の 層のあいだの水蒸気量のばらつき（最大−最小）÷平均 の中央値] 床 {sh['spread_f']:.3f} / 高い所 {sh['spread_h']:.3f}   ひねり 床 {sh['spread_ft']:.3f} / 高い所 {sh['spread_ht']:.3f}")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで上がっていく2つの部屋）を選ぶ
# =====================================================================
EPS_PT = 1.0                                       # 「差がある」の目安（ポイント）。マス目の色分けだけに使う（p は 0 を境に数える）
_SAMPLE = None


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 上がり方（床）が全体の中央値の近く（0.85〜1.15倍）、差（高い所 − 床）が 中央値 g の近く（±0.12）、混ざりの強さ K が中央値の近く（0.6〜1.6倍）、
    はじめの湿度 34〜42%、面積 10〜16 m²、外 0〜8℃、換気 0.8〜1.5 回/h、床の結露・霧なし。その中で 差と上がり方が中央値にいちばん近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    s1 = shown()["s1"]
    up_f, up_h = r["up_f"], r["up_h"]
    diff = up_h - up_f
    kmed = float(np.median(p["K0"]))
    ok = ((up_f >= 0.85 * s1["mf"]) & (up_f <= 1.15 * s1["mf"]) & (np.abs(diff - s1["g"]) <= 0.12)
          & (p["K0"] >= 0.6 * kmed) & (p["K0"] <= 1.6 * kmed) & (p["rh0"] >= 0.34) & (p["rh0"] <= 0.42)
          & (p["A"] >= 10) & (p["A"] <= 16) & (p["To"] >= 0) & (p["To"] <= 8) & (p["ach"] >= 0.8) & (p["ach"] <= 1.5)
          & (r["f"]["floor"] == 0) & (r["h"]["floor"] == 0) & (r["f"]["fog"] == 0) & (r["h"]["fog"] == 0))
    cand = np.nonzero(ok)[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    score = np.abs(diff[cand] - s1["g"]) / 0.12 + np.abs(up_f[cand] / s1["mf"] - 1) / 0.15
    i = int(cand[np.argmin(score)])
    q = {k: float(v[i]) for k, v in p.items()}
    sub = {k: v[i:i + 1] for k, v in p.items()}
    rec = {}
    for w in ("floor", "high"):
        o = simulate(sub, w, rec_every=DT_S)
        rec[w] = dict(t=np.array([x[0] for x in o["rec"]]), rho=np.array([x[1][0] for x in o["rec"]]),
                      rh=np.array([x[2][0] for x in o["rec"]]), out=o)
    _SAMPLE = dict(i=i, p=q, rec=rec, up_f=float(up_f[i]), up_h=float(up_h[i]), diff=float(diff[i]),
                   rh0=float(rec["floor"]["rh"][0]), rh_f=float(rec["floor"]["rh"][-1]), rh_h=float(rec["high"]["rh"][-1]),
                   shelf=q["zs_h"] - BODY_H)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    s = sample()
    p = s["p"]
    print("見本", s["i"], "室温", round(p["Tf"], 1), "℃ ΔT", round(p["dT"], 1), "K 湿度", round(s["rh0"] * 100, 1), "% → 床", round(s["rh_f"] * 100, 1), "/ 高い所", round(s["rh_h"] * 100, 1),
          "| 面積", round(p["A"], 1), "m² 加湿", round(p["m"]), "mL/h 外", round(p["To"], 1), "℃ 換気", round(p["ach"], 2), "K0", round(p["K0"], 4), "向き", int(p["dirn"]),
          "上へ", round(p["hr"], 2), "m 棚", round(s["shelf"], 2), "m 差", round(s["diff"], 2))
    sys.exit(0)


# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, text, thump, tick, whoosh, SR)
from engine.parts import bgra, grid_image, loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.7"                                # 日付欄（公開予定日）

COL_F, INK_F = "#f0a65a", "#a85f14"                # 床（だいだい）
COL_H, INK_H = "#5fb9b2", "#1c6d68"                # 高い所（青緑）
COL_0 = "#d3d1c8"                                  # 差が1ポイント未満（灰）
WALL, WALL_S = "#8aa6bd", "#7d9ab2"
FLOORC = "#c8a578"

# 並びと正解は ここ（と comment.txt）だけ。答えは「ほぼ同じ」なので 正解が A の位置になるよう 並べた。
# 答えが変わったら LABELS・CORRECT も合わせる（run_checks が確かめる）
LABELS = ["ほぼ同じ", "床", "高い所"]
CORRECT = 0                                        # answer_by_rule の結果の位置（0始まり。0 = A）
KEY_LABEL = {"same": "ほぼ同じ", "floor": "床", "high": "高い所"}
CATS = ("high", "floor", "same")                   # マス目の分け方（高い所が1pt以上多く上がった / 床が1pt以上 / 差1pt未満）
CAT_COL = {"high": COL_H, "floor": COL_F, "same": COL_0}

BIG_Q = ["加湿器、床に置く？", "高い所に置く？"]                            # 定位置（上）の2行
BIG_Q3 = ["加湿器、", "床に置く？", "高い所に置く？"]                       # 1コマ目の3行（同じ大きさ）
DETAIL = "部屋の真ん中の湿度が早く上がるのは？"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                             # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 16.0                                    # T_GO から1時間後まで
R0 = 1.4                                           # 冒頭の進み（シミュの分／動画の秒）

# 画面の置き場所
PX0, PX1, PY0, PY1 = 80.0, 1020.0, 830.0, 1480.0
RW = 468.0
RX = {"f": 80.0, "h": 552.0}                       # 部屋の左端
FLOOR_Y = 1400.0
Z_PX = (FLOOR_Y - PY0) / ROOM_H                    # 1 m あたりのピクセル
BED_X = 550.0
CD_X, CD_Y = 550.0, 1290.0


def zy(z):
    return FLOOR_Y - Z_PX * z


def setup():
    global TL, RX_, T_FIN, T_G0, T_G1, T_REV, T_ANS2, T_TW, T_TW_G, T_TW_RES, T_Q, DURATION
    sample()
    dmin = HOUR / 60.0
    T_FIN = T_GO + RACE_LEN

    def build(rx):
        ts = np.arange(0, 70, 1 / 200)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.2) for t in ts]))
        return ts, np.cumsum(sp) / 200

    lo, hi = 1.0, 600.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN, ts, tau)) > dmin:
            hi = mid
        else:
            lo = mid
    RX_ = hi
    ts, tau = build(RX_)
    TL = dict(t=ts, tau=tau)
    T_G0 = T_FIN + 1.7
    T_G1 = T_G0 + 2.6
    T_REV = T_G1 + 2.6
    T_ANS2 = T_REV + 1.7
    T_TW = T_ANS2 + 3.4                            # ひねり（問い）
    T_TW_G = T_TW + 0.8                            # ひねりのマス目が埋まり始める
    T_TW_RES = T_TW_G + 2.4                        # ひねりの数字
    T_Q = T_TW_RES + 3.4
    DURATION = T_Q + 4.4


def tau_of(t):
    """その時刻の「加湿器をつけてからの経過（分）」"""
    return min(float(np.interp(t, TL["t"], TL["tau"])), HOUR / 60.0)


def frac_hour(t):
    return clamp01(tau_of(t) / (HOUR / 60.0))


def layers_at(t, w):
    """その時刻の 各層の水蒸気量（w = 'floor' / 'high'）と 顔の高さの相対湿度"""
    rec = sample()["rec"][w]
    tt = tau_of(t) * 60.0
    rho = np.array([np.interp(tt, rec["t"], rec["rho"][:, i]) for i in range(NL)])
    return rho, float(np.interp(tt, rec["t"], rec["rh"]))


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def clip_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    ctx.clip()


def border_panel(ctx):
    core.rrect(ctx, PX0, PY0, PX1 - PX0, PY1 - PY0, 22)
    _stroke(ctx, 3.5, INK, 0.75)


ZOOM0, ZOOM_T = 1.3, 1.3


def zoom_art(ctx, t, x0):
    """絵だけ、冒頭にぐっと引く（枠の中で動く。カードの字は動かさない）。寄りの中心は 部屋の左下（ふき出し口のあたり）"""
    z = 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))
    cx, cy = x0 + 150.0, 1250.0
    ctx.translate(cx, cy)
    ctx.scale(z, z)
    ctx.translate(-cx, -cy)


# ---------- 部屋の背景 ----------

def draw_bg(ctx, x0):
    fill(ctx, hexrgb(WALL))
    ctx.rectangle(x0, PY0, RW, FLOOR_Y - PY0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(WALL_S, 0.9))                          # 壁のしま
    for x in range(int(x0) - 20, int(x0 + RW) + 20, 36):
        ctx.rectangle(x, PY0, 14, FLOOR_Y - PY0)
        ctx.fill()
    fill(ctx, hexrgb(FLOORC))                                          # 床
    ctx.rectangle(x0, FLOOR_Y, RW, PY1 - FLOOR_Y)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#a98a5f", 0.7))
    ctx.set_line_width(2.5)
    for i in range(0, 9):
        ctx.move_to(x0 + i * 62 - 8, FLOOR_Y + 8)
        ctx.line_to(x0 + i * 62 - 40, PY1)
    ctx.stroke()
    ctx.rectangle(x0, FLOOR_Y - 8, RW, 12)                             # 幅木
    ctx.set_source_rgba(*hexrgb("#f4eee0", 1))
    ctx.fill()


def draw_window(ctx, x0, t):
    wx0, wy0, ww, wh = x0 + 332, 925.0, 118.0, 120.0
    core.rrect(ctx, wx0, wy0, ww, wh, 6)
    fill(ctx, hexrgb("#f4eee0"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.85)
    g = cairo.LinearGradient(0, wy0, 0, wy0 + wh)
    g.add_color_stop_rgb(0, *hexrgb("#6b7fb5")[:3])
    g.add_color_stop_rgb(1, *hexrgb("#d9a98f")[:3])
    ctx.set_source(g)
    ctx.rectangle(wx0 + 8, wy0 + 8, ww - 16, wh - 16)
    ctx.fill()
    ctx.move_to(wx0 + ww / 2, wy0 + 8)
    ctx.line_to(wx0 + ww / 2, wy0 + wh - 8)
    _stroke(ctx, 4, "#f4eee0", 1.0)


def draw_aircon(ctx, x0, t):
    """暖房（壁の上）。あたたかい風が、見本の回の向きに流れる"""
    ax0, ay0, aw, ah = x0 + 306, 846.0, 156.0, 46.0
    core.rrect(ctx, ax0, ay0, aw, ah, 10)
    fill(ctx, hexrgb("#f7f3ea"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    ctx.rectangle(ax0 + 12, ay0 + ah - 12, aw - 24, 5)
    fill(ctx, hexrgb("#c9c4b6"))
    ctx.fill()
    d = int(sample()["p"]["dirn"])
    vx, vy = ((0.0, 1.0), (-1.0, 0.25), (-0.8, -0.0))[d]                # 下向き／水平／上向き（天井ぞい）
    sx, sy = (ax0 + aw / 2, ay0 + ah) if d == 0 else (ax0 + 14, ay0 + ah * 0.6)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for j in range(3):
        for k in range(3):
            u = ((t * 0.9 + k / 3.0 + j * 0.11) % 1.0)
            L = 120.0
            px, py = sx + (j - 1) * (30 if d == 0 else 0) + vx * L * u, sy + (0 if d == 0 else (j - 1) * 14) + vy * L * u
            a = 0.8 * math.sin(u * math.pi)
            ctx.move_to(px - vx * 16, py - vy * 16)
            ctx.line_to(px, py)
            _stroke(ctx, 6, "#ee8a4a", a)


# ---------- 家具・人 ----------

def draw_shelf(ctx, x0, sh):
    top = zy(sh)
    core.rrect(ctx, x0 + 8, top, 118, FLOOR_Y - top, 6)
    fill(ctx, hexrgb("#b98f62"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    core.rrect(ctx, x0 + 2, top - 10, 130, 14, 5)                      # 天板
    fill(ctx, hexrgb("#d3ad7c"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    mid = x0 + 67
    ctx.move_to(mid, top + 14)
    ctx.line_to(mid, FLOOR_Y - 6)
    _stroke(ctx, 3, INK, 0.6)
    for kx in (mid - 12, mid + 12):
        ctx.arc(kx, (top + FLOOR_Y) / 2, 4.5, 0, 2 * math.pi)
        fill(ctx, hexrgb("#f4eee0"))
        ctx.fill()


def draw_unit(ctx, x0, zs, base_z):
    """加湿器の本体。ふき出し口の高さが zs"""
    cx = x0 + 67
    ny = zy(zs)
    by = zy(base_z)
    top = ny + 14
    core.rrect(ctx, cx - 32, top, 64, by - top, 14)
    fill(ctx, hexrgb("#f7f3ea"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    core.rrect(ctx, cx - 20, top + 12, 40, max(12.0, by - top - 24), 8)    # 水のタンク
    fill(ctx, hexrgb("#8fcdf0"))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.6)
    core.rrect(ctx, cx - 11, ny, 22, 18, 5)                            # ふき出し口
    fill(ctx, hexrgb("#c9c4b6"))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.85)


def draw_sofa_person(ctx, x0, t):
    cx = x0 + 366
    sw = 198.0
    # ソファ（うしろ・座面・ひじかけ）
    core.rrect(ctx, cx - sw / 2 + 14, 1186, sw - 28, 150, 22)
    fill(ctx, hexrgb("#c97b6b"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    core.rrect(ctx, cx - sw / 2, 1290, sw, 110, 18)
    fill(ctx, hexrgb("#d68b7a"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.85)
    for sx in (-1, 1):
        core.rrect(ctx, cx + sx * (sw / 2 - 17) - 17, 1240, 34, 160, 14)
        fill(ctx, hexrgb("#c97b6b"))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.85)
    br = 1.0 + 0.01 * math.sin(2 * math.pi * 0.4 * t)
    # 足
    for sx in (-1, 1):
        core.rrect(ctx, cx + sx * 24 - 19, 1298, 38, 92, 14)
        fill(ctx, hexrgb("#4c5f8a"))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
        core.rrect(ctx, cx + sx * 30 - 24, 1384, 48, 20, 10)
        fill(ctx, hexrgb("#f4eee0"))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.9)
    # からだ・腕
    ctx.save()
    ctx.translate(cx, 1300)
    ctx.scale(1, br)
    ctx.translate(-cx, -1300)
    core.rrect(ctx, cx - 56, 1210, 112, 108, 30)
    fill(ctx, hexrgb("#f2cd5d"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    for sx in (-1, 1):
        core.rrect(ctx, cx + sx * 66 - 15, 1222, 30, 92, 15)
        fill(ctx, hexrgb("#f2cd5d"))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
        ctx.arc(cx + sx * 66, 1318, 15, 0, 2 * math.pi)
        fill(ctx, hexrgb("#ffe2c9"))
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
    ctx.restore()
    # あたま（顔の高さ ＝ 湿度計の高さ）
    hx, hy, hr = cx, zy(Z_FACE) - 2, 52.0
    ctx.arc(hx, hy, hr, 0, 2 * math.pi)
    fill(ctx, hexrgb("#ffe2c9"))
    ctx.fill_preserve()
    _stroke(ctx, 4.0, INK, 0.9)
    ctx.new_path()
    ctx.arc(hx, hy, hr + 3, math.pi * 1.02, math.pi * 1.98)
    ctx.curve_to(hx + 44, hy - 32, hx + 24, hy - 24, hx + 12, hy - 28)
    ctx.curve_to(hx + 4, hy - 20, hx - 14, hy - 30, hx - 24, hy - 26)
    ctx.curve_to(hx - 32, hy - 22, hx - 42, hy - 28, hx - hr - 3, hy - 2)
    ctx.close_path()
    fill(ctx, hexrgb("#4d3526"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    blink = 0.15 if (t % 3.2) > 3.05 else 1.0
    for sx in (-1, 1):
        ex = hx + sx * 20
        ctx.save()
        ctx.translate(ex, hy + 8)
        ctx.scale(1, blink)
        ctx.arc(0, 0, 5.5, 0, 2 * math.pi)
        fill(ctx, hexrgb(INK))
        ctx.fill()
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#ff9f9a", 0.55))
        ctx.arc(hx + sx * 34, hy + 22, 8, 0, 2 * math.pi)
        ctx.fill()
    ctx.new_path()
    ctx.arc(hx, hy + 16, 12, 0.2 * math.pi, 0.8 * math.pi)
    _stroke(ctx, 3.5, "#c8665e", 0.95)


# ---------- 湿度計 ----------

GAUGE_DX = 188.0


def draw_gauge(ctx, x0, t, k):
    cx, cy = x0 + GAUGE_DX, zy(Z_FACE)
    ctx.rectangle(cx - 4, cy + 56, 8, FLOOR_Y - cy - 56)
    fill(ctx, hexrgb("#7d6b52"))
    ctx.fill()
    ctx.save()
    ctx.translate(cx, FLOOR_Y - 2)
    ctx.scale(1, 0.32)
    ctx.arc(0, 0, 44, 0, 2 * math.pi)
    ctx.restore()
    fill(ctx, hexrgb("#7d6b52"))
    ctx.fill()
    core.rrect(ctx, cx - 76, cy - 60, 152, 120, 16)
    fill(ctx, hexrgb("#fffdf6"))
    ctx.fill_preserve()
    _stroke(ctx, 4.5, INK, 0.9)
    w = "floor" if k == "f" else "high"
    rho, rh = layers_at(t, w)
    ink = INK_F if k == "f" else INK_H
    text(ctx, "湿度", cx, cy - 33, 26, PENCIL, bold=False)
    text(ctx, f"{int(math.floor(rh * 100 + 0.5))}%", cx, cy + 12, 62, ink)


# ---------- 霧（水蒸気）----------

_PUFF = np.random.default_rng(11).random((24, 64, 4))
EX_SCALE = 3.2                                     # この水蒸気量の増え（g/m³）で いちばん濃い霧


def draw_haze(ctx, x0, t, k):
    """各層の水蒸気の増え（g/m³）に比例した白いもや。モデルの層の値そのもの"""
    w = "floor" if k == "f" else "high"
    rho, _ = layers_at(t, w)
    ex = np.maximum(rho - sample()["rec"][w]["rho"][0], 0.0)
    al = 0.55 * np.minimum(ex / EX_SCALE, 1.0) ** 0.8
    g = cairo.LinearGradient(0, FLOOR_Y, 0, PY0)
    g.add_color_stop_rgba(0.0, 1, 1, 1, float(al[0]))
    for i in range(NL):
        g.add_color_stop_rgba((i + 0.5) / NL, 1, 1, 1, float(al[i]))
    g.add_color_stop_rgba(1.0, 1, 1, 1, float(al[-1]))
    ctx.set_source(g)
    ctx.rectangle(x0, PY0, RW, FLOOR_Y - PY0)
    ctx.fill()


def draw_puffs(ctx, x0, t, k, zs):
    """ふき出し口から出る もや（絵だけの粒。上へ届く高さは見本の回の値）"""
    s = sample()
    nx, ny = x0 + 67, zy(zs) - 4
    rise = s["p"]["hr"] * Z_PX
    NP, LIFE = 24, 2.0
    for j in range(NP):
        tt = t + j * LIFE / NP
        age = (tt % LIFE) / LIFE
        idn = int(tt // LIFE) % 64
        r0, r1, r2, r3 = _PUFF[j, idn]
        y = ny - rise * (1 - (1 - age) ** 1.7) * (0.75 + 0.25 * r1)
        x = nx + (50 + 110 * r0) * age ** 1.1 + 7 * math.sin(age * 6 + r2 * 6)
        rad = 9 + 30 * age ** 0.8 * (0.8 + 0.4 * r3)
        a = 0.62 * (1 - age) ** 0.9 * min(1.0, age * 10)
        ctx.set_source_rgba(1, 1, 1, a)
        ctx.arc(x, y, rad, 0, 2 * math.pi)
        ctx.fill()


# ---------- 場面 ----------

def draw_label(ctx, k):
    x0 = RX[k]
    lab = "床に置く" if k == "f" else "高い所に置く"
    w = core.text_width(lab, 36) + 30
    core.rrect(ctx, x0 + 12, 838, w, 46, 12)                           # 札
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, PENCIL, 0.7)
    text(ctx, lab, x0 + 12 + w / 2, 862, 36, INK_F if k == "f" else INK_H)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_room(ctx, t, k):
    x0 = RX[k]
    s = sample()
    ctx.save()
    ctx.rectangle(x0, PY0, RW, PY1 - PY0)
    ctx.clip()
    draw_bg(ctx, x0)
    draw_window(ctx, x0, t)
    draw_aircon(ctx, x0, t)
    zs = s["p"]["zs_f"] if k == "f" else s["p"]["zs_h"]
    if k == "h":
        draw_shelf(ctx, x0, s["shelf"])
    draw_sofa_person(ctx, x0, t)
    draw_unit(ctx, x0, zs, 0.0 if k == "f" else s["shelf"])
    draw_haze(ctx, x0, t, k)
    draw_puffs(ctx, x0, t, k, zs)
    draw_gauge(ctx, x0, t, k)
    ctx.restore()


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    ctx.push_group()
    ctx.save()
    clip_panel(ctx)
    for k in ("f", "h"):
        ctx.save()
        ctx.rectangle(RX[k], PY0, RW, PY1 - PY0)                       # 部屋ごとに はみ出さないように
        ctx.clip()
        zoom_art(ctx, t, RX[k])
        draw_room(ctx, t, k)
        ctx.restore()
    ctx.restore()
    border_panel(ctx)
    ctx.move_to(PX0 + RW + 2, PY0)                                     # 2つの部屋のさかい
    ctx.line_to(PX0 + RW + 2, PY1)
    _stroke(ctx, 4, INK, 0.8)
    s = sample()
    for k in ("f", "h"):
        draw_label(ctx, k)
        if t >= T_FIN and frac_hour(t) >= 0.999:                       # 1時間後: 上がった分を赤ペンで囲む
            u = clamp01((t - T_FIN) / 0.35)
            up = s["up_f"] if k == "f" else s["up_h"]
            cx, cy = RX[k] + GAUGE_DX, zy(Z_FACE)
            text(ctx, f"+{up:.1f}", cx, cy - 114, 42, INK_F if k == "f" else INK_H, alpha=u)
            note.pen_circle(ctx, cx, cy, 92, 80, RED, seed=70 + (k == "h"), width=4.5, progress=u)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


def clock_alpha(t):
    return ease_out((t - T_MOVE) / 0.4) * (1 - ease((t - T_G0) / 0.35)) if t >= T_MOVE else 0.0


def clock_str(t):
    return f"つけて {int(tau_of(t))}分"


def caption_text():
    p = sample()["p"]
    return f"たとえば、この1回では　室温 {p['Tf']:.0f}℃・はじめの湿度 {p['rh0'] * 100:.0f}%・加湿 {p['m']:.0f}mL/h"


def draw_clock(ctx, t):
    a = clock_alpha(t)
    if a <= 0:
        return
    note.sticky(ctx, clock_str(t), 580, 640, 40, "yellow", a=a, tilt=-0.02)
    cap = caption_text()
    sz = 30
    while core.text_width(cap, sz) > 860:
        sz -= 1
    text(ctx, cap, 560, 724, sz, PENCIL, bold=False, alpha=a)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 5
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 660.0
_GRID = {}


def cat_array(s):
    """試行ごとの分類 0 = 高い所が1pt以上多く上がった / 1 = 床が1pt以上 / 2 = 差が1pt未満"""
    c = np.full(N_TRIAL, 2, int)
    c[s["diff"] >= EPS_PT] = 0
    c[s["diff"] <= -EPS_PT] = 1
    return c


def grid_surface(n, n2):
    """先頭 n2 マスはひねり（エアコンの風）の分類、それ以降は ふつうの分類"""
    key = (int(n) // G_COLS, int(n2) // G_COLS)
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 4:
        _GRID.clear()
    sh = shown()
    c1, c2 = cat_array(sh["s1"]), cat_array(sh["s2"])
    pal = np.array([bgra(CAT_COL[c]) for c in CATS], np.uint8)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    flat = cols.reshape(-1, 4)
    m = min(N_TRIAL, key[0] * G_COLS)
    m2 = min(N_TRIAL, key[1] * G_COLS)
    flat[:m] = pal[c1[:m]]
    flat[:m2] = pal[c2[:m2]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def g_text(g):
    """上がり方の差（高い所 − 床）の言い方"""
    if abs(g) < 0.05:
        return "差は ほぼ0ポイント"
    return f"{'床' if g < 0 else '高い所'}のほうが {abs(g):.1f}ポイント上"


def stat_text(s):
    return f"この部屋の置き方なら、\n上がり方の差は 中央値で\n{g_text(s['g'])}\n高い所が上だった回は 約{pct_i(s['p'])}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    n2 = N_TRIAL * clamp01((t - T_TW_G) / 1.4) if t >= T_TW_G else 0
    surf, _ = grid_surface(n, n2)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    if t < T_TW:
        text(ctx, f"{fmt(n)} / 10,000回　1マス＝1回", 580, 616, 32, INK, alpha=a)
    else:
        text(ctx, f"エアコンの風　{fmt(max(n2, 0))} / 10,000回", 580, 616, 32, INK, alpha=a)
    c1 = cat_array(sh["s1"])
    m = (int(n) // G_COLS) * G_COLS
    lg = 1 - ease((t - T_REV) / 0.3)
    if lg > 0 and t < T_TW:
        labs = {"high": "高い所が1ポイント以上多く上がった", "floor": "床が1ポイント以上多く上がった", "same": "差は1ポイント未満"}
        for i, cat in enumerate(CATS):
            y = 1105 + i * 46
            cnt = int((c1[:m] == i).sum())
            fill(ctx, hexrgb(CAT_COL[cat], a * lg))
            ctx.rectangle(130, y - 15, 30, 30)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(INK, 0.7 * a * lg))
            ctx.set_line_width(2)
            ctx.rectangle(130, y - 15, 30, 30)
            ctx.stroke()
            text(ctx, labs[cat], 176, y, 30, INK, align="left", alpha=a * lg)
            text(ctx, f"{fmt(cnt)}回", 925, y, 30, INK, align="right", alpha=a * lg)
        if t >= T_G1 + 0.3:
            b = ease_out((t - T_G1 - 0.3) / 0.3) * a * lg
            note.sticky(ctx, stat_text(sh["s1"]), 540, 1330, 32, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- 答え ----------

def answer_key():
    s1 = shown()["s1"]
    return answer_by_rule(s1["p"], s1["g"])


def reason_text():
    sh = shown()
    k = answer_key()
    sp = 100 * 0.5 * (sh["spread_f"] + sh["spread_h"])
    head = f"この部屋の置き方なら、1時間後の\n高さごとの水蒸気量の差は 約{sp:.0f}%\n"
    if k == "same":
        return head + "部屋じゅうに混ざって 置き場所の差は消える"
    if k == "high":
        return head + "高い所のほうが 顔の高さに届きやすい"
    return head + "床のほうが 顔の高さに届きやすい"


def twist_text():
    return stat_text(shown()["s2"])


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3) * (1 - ease((t - T_TW) / 0.3))
    note.sticky(ctx, f"残念、{KEY_LABEL[key]}が正解。", 580, 1140, 54, "yellow", fg=RED, a=b, tilt=-0.02)
    text(ctx, "（この部屋の置き方なら）", 580, 1218, 30, PENCIL, bold=False, alpha=b)   # 統括 10/27: 「ほぼ同じ」に必ず添える
    if t >= T_ANS2:
        c = ease_out((t - T_ANS2) / 0.3) * (1 - ease((t - T_TW) / 0.3))
        note.sticky(ctx, reason_text(), 540, 1330, 32, "blue", a=c, tilt=0.012)
    if t >= T_TW:                                                      # ひねり
        d = ease_out((t - T_TW) / 0.3)
        note.sticky(ctx, "では、エアコンの風が\n当たる所に置いたら？", 580, 1140, 38, "yellow", a=d, tilt=-0.02)
    if t >= T_TW_RES:
        e = ease_out((t - T_TW_RES) / 0.3)
        note.sticky(ctx, twist_text(), 540, 1330, 32, "pink", fg=RED, a=e, tilt=0.012)


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


def big3_size(max_w=860.0, cap=100.0):
    """3行とも同じ大きさ。いちばん長い行が max_w に収まる大きさ（行の間隔の都合で cap まで）"""
    return min(cap, 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3))


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（同じ大きさ）・補足・三択（横1列）。その下に2つの部屋（0秒目から湯気が出て、場面が引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = big3_size(860.0)
        ys = (450, 552, 654)
        for line, y in zip(BIG_Q3, ys):
            pop = 1 + 0.03 * (1 - ease_out(t / 0.4))
            ctx.save()
            ctx.translate(565, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q3[2], sz)
        note.pen_line(ctx, 565 - w2 / 2 - 6, 702, 565 + w2 / 2 + 6, 698, RED, seed=5, width=8,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 565, 742, 32, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 42, 565, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            y = 792
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
        sz = 47.0
        text(ctx, BIG_Q[0], 540, 402, sz, INK, alpha=m)
        text(ctx, BIG_Q[1], 540, 456, sz, INK, alpha=m)
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 540 - w2 / 2 - 6, 488, 540 + w2 / 2 + 6, 485, RED, seed=5, width=6, alpha=m)
        rev = clamp01((t - reveal_t) / 0.5) if reveal_t is not None else 0.0
        y = 540
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840)):
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


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_clock(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたの家の加湿器、\nどこに置いていますか？", 580, 860, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 0.9) / 0.3)
        text(ctx, "コメントで教えてください", 580, 1050, 36, INK, bold=False, alpha=r)


def scene(ctx, t):
    note.paper(ctx)
    body(ctx, t)
    INTRO.draw(ctx, t, reveal_t=T_REV)


def draw(ctx, t):
    scene(ctx, t)
    loop_back(ctx, t, DURATION, scene)


# ---------- 音 ----------

def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)                          # 湯気が吹き出す
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.32)
    for k in range(int(T_MOVE) + 1):
        mx.add(float(k), tick(2400, 0.02), 0.2)
    for k, w, f0 in (("f", "floor", 880.0), ("h", "high", 1046.5)):    # 湿度計が1%上がるごとに
        rh = s["rec"][w]["rh"]
        tsec = s["rec"][w]["t"]
        shown_pct = np.floor(rh * 100 + 0.5)
        v0 = int(shown_pct[0])
        for v in range(v0 + 1, int(shown_pct[-1]) + 1):
            idx = int(np.argmax(shown_pct >= v))
            tt = float(np.interp(tsec[idx] / 60.0, TL["tau"], TL["t"]))
            if T_GO <= tt <= T_FIN:
                mx.add(tt + (0.0 if k == "f" else 0.02), blip(f0, 0.04), 0.07)
    mx.add(T_FIN - 0.4, bell(784.0, 1.4), 0.45)             # 1時間後
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                     # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, blip(659.3, 0.14), 0.3)                    # ひねり
    mx.add(T_TW_G - 0.3, riser(0.5), 0.35)
    mx.add(T_TW_RES, blip(784.0, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    p = r["p"]
    s1, s2 = sh["s1"], sh["s2"]
    checks = []
    # (1) 飽和水蒸気量: 20℃ で約 17.3 g/m³、20℃・60% の水蒸気量は 約12℃ の飽和量と同じ（露点）
    checks.append(("飽和水蒸気量（20℃）が約17.3 g/m³", float(rho_sat(20.0)), 17.3, 0.1))
    checks.append(("20℃・60% の水蒸気圧 ＝ 露点（約12℃）の飽和水蒸気圧（hPa）", float(0.6 * es_hpa(20.0)), float(es_hpa(12.0)), 0.05))
    # (2) 水のつり合い（全回・4つの場合）: 出した量 ＝ 空気の増え ＋ 換気で出た量 ＋ ため池 ＋ 床 ＋ 窓 ＋ 霧
    for name, o in (("床", r["f"]), ("高い所", r["h"]), ("床・風", r["ft"]), ("高い所・風", r["ht"])):
        vol = p["A"] * DZ
        d_air = ((o["rho"] - (p["rh0"] * rho_sat(p["Tf"]))[:, None]) * vol[:, None]).sum(axis=1)
        resid = o["inj"] - (d_air + o["vent"] + o["buf"] + o["floor"] + o["win"] + o["fog"])
        checks.append((f"水のつり合いの残り・{name}（最大・g）", float(np.max(np.abs(resid))), 0.0, 1e-6))
    # (3) 湿度が100%を超えない（全層・全回）
    ok = all(bool(np.all(o["rho"] <= o["rs"] + 1e-9)) for o in (r["f"], r["h"], r["ft"], r["ht"]))
    checks.append(("湿度が100%を超えない（全層・全回）", float(ok), 1.0, 0.0))
    # (4) 極限: 換気なし・ため池なし・結露なし・混ざりが強い → 部屋の水蒸気量が 出した量どおり（顔の高さの湿度の上がり方）
    n_ = 400
    d1 = {k: v[:n_].copy() for k, v in p.items()}
    d1.update(ach=np.zeros(n_), tau=np.full(n_, 1e12), To=d1["Tf"].copy(), K0=np.full(n_, 5.0), boost=np.ones(n_), qk=np.ones(n_),
              tfs=np.full(n_, 60.0), m=np.minimum(d1["m"], 0.05 * 17.3 * d1["A"] * ROOM_H), hr=np.full(n_, 1.0))
    o1 = simulate(d1, "floor")
    exact = d1["rh0"] * rho_sat(d1["Tf"]) + d1["m"] / (d1["A"] * ROOM_H)           # 1時間ぶん
    exact_rh = exact / (rho_sat(temp_profile(d1))[:, FACE_L])
    checks.append(("換気なし・ため池なし・結露なし・十分に混ぜたときの湿度（最大のずれ・ポイント）",
                   float(np.max(np.abs(o1["rh1"] - exact_rh)) * 100), 0.0, 0.05))
    # (5) 混ざりが十分強ければ 置き場所で変わらない（同じ極限の条件で 床と高い所の差）
    o2 = simulate(d1, "high")
    checks.append(("極限で 床と高い所の湿度の差（最大・ポイント）", float(np.max(np.abs(o1["rh1"] - o2["rh1"])) * 100), 0.0, 0.05))
    # (6) 見本は1万回の中の1回で、値が全体の中央値の近く
    s = sample()
    i = s["i"]
    checks.append(("見本の湿度（床）が1万回の値と同じ", s["rh_f"], float(r["f"]["rh1"][i]), 1e-9))
    checks.append(("見本の湿度（高い所）が1万回の値と同じ", s["rh_h"], float(r["h"]["rh1"][i]), 1e-9))
    checks.append(("見本の差が中央値 g の近く（±0.12）", s["diff"], s1["g"], 0.12))
    checks.append(("見本の上がり方（床）が中央値の近く（±15%）", s["up_f"], s1["mf"], 0.15 * s1["mf"]))
    checks.append(("見本の「上がった分」が 湿度計の値の差と同じ（床・ポイント）", (s["rh_f"] - s["rh0"]) * 100, s["up_f"], 1e-9))
    # (7) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ（正解は A の位置）
    key = answer_by_rule(s1["p"], s1["g"])
    checks.append(("画面の正解の位置が 規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A", float(INTRO.correct), 0.0, 0.0))
    checks.append(("LABELS が 床・ほぼ同じ・高い所 の3つ", float(sorted(LABELS) == sorted(KEY_LABEL.values())), 1.0, 0.0))
    # (8) 回数が足して1万
    checks.append(("分類の合計（ふつう）", float(s1["n_hi"] + s1["n_fl"] + s1["n_eq"]), float(N_TRIAL), 0.0))
    checks.append(("分類の合計（ひねり）", float(s2["n_hi"] + s2["n_fl"] + s2["n_eq"]), float(N_TRIAL), 0.0))
    # (9) 画面の数字: マス目の数と分類の数が合う
    ca = cat_array(s1)
    checks.append(("マス目の「高い所が1pt以上」の数", float((ca == 0).sum()), float((s1["diff"] >= EPS_PT).sum()), 0.0))
    checks.append(("マス目の3つの合計が1万", float(sum(int((ca == c).sum()) for c in range(3))), float(N_TRIAL), 0.0))
    # (10) 1時間の上がり方が常識的（中央値が 数〜十数ポイント）
    checks.append(("1時間の上がり方（中央値・ポイント）が 数〜十数", float(np.median(np.concatenate([r["up_f"], r["up_h"]]))), 10.0, 7.0))
    check_answers(checks)


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


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  早送り {RX_:.1f}分/秒  1時間後 {T_FIN:.2f}  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW_G:.1f}/{T_TW_RES:.1f}  "
          f"締め {T_Q:.1f}  見本 {s['i']}（湿度 {s['rh0'] * 100:.0f}% → 床 {s['rh_f'] * 100:.1f}% / 高い所 {s['rh_h'] * 100:.1f}%）")
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", twist_text().replace("\n", " / "))
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 0.8, 1.2, 2.5, 4.4, 5.2, 6.5, 9.0, 12.0, 15.0, 18.0, T_FIN - 0.4, T_FIN + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.5, T_TW + 0.5, T_TW_G + 1.8, T_TW_RES + 0.6, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
