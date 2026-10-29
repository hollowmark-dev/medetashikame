"""2200年前の人は、棒1本で地球の大きさを当てた？【1万回やり直した結果】（横型ロング・チャンネル「めでたしかめ」）

このファイルは公開日まで非公開（答えが書いてある）。公開 11/7（土）19:00。
前半はモデル（数字の計算・照合・数字の書き出し）。後半（「# ここから下は場面」から）が場面（描画・音・照合・書き出し。inoh-long.py と同じ並び）。
モデルの計算は下絵 sims/chikyu-long.draft.py と同じ（同じ種・同じ順番で乱数を引く＝出力の数字が一致する。--numbers が下絵を実際に走らせて1行ずつ突き合わせる）。

■ モデル（下絵のとおり。値は【仮定】または資料の値。動画で「〜と置きます」と言う）
  置き方   : 夏至の正午。シエネ（今のアスワン）は太陽がほぼ真上、アレクサンドリアでは棒の影ができる。
             エラトステネスのやり方 ＝ 地球一周 ＝ 2都市の距離 × 360 ÷ アレクサンドリアの影の角度（シエネの角度は0とみなす）
  1回ごとの : 影の長さの読み取り（1回・±1.5cm）／影の先をどこで読むかの癖（太陽の見かけの半径 ±0.265° の幅で一様・その人の癖として回ごとに固定）
             ／距離の測り方の偏り（回ごとに固定・割合）
  段       : 1 棒1m・目で読む・距離±10% → 2 ＋棒を10mに → 3 ＋距離を±2%に → 4 ＋10日測って平均 → 5 ＋影の先をくっきり
  当たり   : 本当の値（北極・南極を回る向きの一周 40,008km）から ±10% 以内（後半は ±5% 以内）。ずれの中央値 ＝ ずれ（割合）の中央値
  町が近い : 同じ経線上に d km 離れた2つの町（段1の測り方と段5の測り方）。南の町の太陽の傾きは正しく引いて測る
  入れていないもの: 大気による光の曲がり・地球が完全な球でないこと・正午の時刻のずれ

使い方
  python -X utf8 sims/chikyu-long.py --numbers                 計算 → 下絵と突き合わせ → 照合 → out/chikyu-long/data.json・numbers.md
  python -X utf8 sims/chikyu-long.py --check                   data.json を読んで照合だけ
  python -X utf8 sims/chikyu-long.py --scenecheck --fake-voice 場面の照合（音声なし・長さは見積もり）
  python -X utf8 sims/chikyu-long.py --stills --fake-voice     要所の静止画と sheet_480.png（out/chikyu-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
  python -X utf8 sims/chikyu-long.py --wraps | --readings | --docs | --anchors --fake-voice
  python -X utf8 sims/chikyu-long.py --preview                 960×540 の確認用動画（AivisSpeech の音声）
  （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SLUG = "chikyu-long"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "out" / SLUG
DRAFT = ROOT / "sims" / "chikyu-long.draft.py"

# ============================================================
# 0. 置いた値（下絵と同じ）
# ============================================================
N = 10_000
SEED = 20261107
LAT_S, LON_S = 24.09, 32.90      # アスワン（シエネ・事実確認 2026-10-25）
LAT_A, LON_A = 31.20, 29.89      # アレクサンドリア（事実確認 2026-10-25）
EPS = 23.72                      # 紀元前240年ごろの地軸の傾き 23°43′
R = 6371.0
C_TRUE = 40_008.0                # 子午線方向の一周（km）
SUN_HALF = 0.265                 # 太陽の見かけの半径（度）


def gc_km(la1, lo1, la2, lo2):
    p1, p2 = math.radians(la1), math.radians(la2)
    dl = math.radians(lo2 - lo1)
    c = math.sin(p1) * math.sin(p2) + math.cos(p1) * math.cos(p2) * math.cos(dl)
    return R * math.acos(c)


D_GC = gc_km(LAT_S, LON_S, LAT_A, LON_A)          # 2都市の大圏距離
D_MER = (LAT_A - LAT_S) / 360 * C_TRUE            # 南北の成分だけ
Z_A = LAT_A - EPS                                  # アレクサンドリアの天頂からの角度
Z_S = LAT_S - EPS                                  # シエネ（0ではない）
D_EW = math.sqrt(max(D_GC ** 2 - D_MER ** 2, 0.0))  # 東西にずれた分（図用。画面には出さない）


def run(stage, rng, H=1.0, sig_L=0.015, n_days=1, blur=SUN_HALF, sig_D=0.10, D_base=None, z=None, z0=0.0):
    """1万回の結果（km の配列）を返す（下絵の run と同じ）。
    H: 棒の高さ(m)  sig_L: 影の長さの読み取りのぶれ(m・1回)  n_days: 測って平均する日数
    blur: 影の先をどこで読むかの癖（±度・その人の癖として回ごとに固定）
    sig_D: 距離の測り方の偏り（割合・回ごとに固定）
    """
    D_base = D_GC if D_base is None else D_base
    z = Z_A if z is None else z
    L_true = H * math.tan(math.radians(z))
    e_L = rng.normal(0, sig_L, (N, n_days)).mean(axis=1)
    habit = rng.uniform(-blur, blur, N)
    theta = np.degrees(np.arctan((L_true + e_L) / H)) + habit - z0
    D = D_base * (1 + rng.normal(0, sig_D, N))
    return D * 360 / theta, theta


def stats(C, ref=C_TRUE):
    err = (C - ref) / ref
    return dict(med=float(np.median(C)), p10=float(np.percentile(C, 10)), p90=float(np.percentile(C, 90)),
                w10=float(np.mean(np.abs(err) <= 0.10)), w5=float(np.mean(np.abs(err) <= 0.05)),
                mad=float(np.median(np.abs(err))), n10=int(np.sum(np.abs(err) <= 0.10)), n5=int(np.sum(np.abs(err) <= 0.05)),
                n_neg=int(np.sum(C <= 0)), n_over=int(np.sum(C > 100_000)))


def row_text(name, s):
    """下絵の summary() が出す1行と同じ書式"""
    return (f"{name:<28} 真ん中 {s['med']:8,.0f}km  1〜9割 {s['p10']:8,.0f}〜{s['p90']:8,.0f}  "
            f"±10%以内 {s['w10']:6.1%}  ±5%以内 {s['w5']:6.1%}  ずれの真ん中 {s['mad']:5.1%}")


def breakdown(H, sig_L, n_days, blur, sig_D, z=Z_A):
    """ぶれの大きさの内訳（答えの割合・1つずつ別々に見たときの標準偏差。デルタ法）。絵の棒の長さだけに使う（数字は画面に出さない）"""
    L = H * math.tan(math.radians(z))
    dth = math.degrees(1.0 / (H * (1.0 + (L / H) ** 2)))          # 影が1m読み違えたときの角度（度）
    return dict(distance=sig_D, reading=dth * sig_L / math.sqrt(n_days) / z, habit=(blur / math.sqrt(3)) / z)


STEPS = [  # (id, 名前（下絵と同じ）, run の引数)
    ("S1", "1 棒1m・影を目で読む・距離±10%", dict()),
    ("S2", "2 ＋棒を10mに", dict(H=10.0)),
    ("S3", "3 ＋距離を±2%に", dict(H=10.0, sig_D=0.02)),
    ("S4", "4 ＋10日測って平均", dict(H=10.0, sig_D=0.02, n_days=10)),
    ("S5", "5 ＋影の先をくっきり", dict(H=10.0, sig_D=0.02, n_days=10, blur=0.05)),
]
TWIST = ("S6", "  ぼやけ±0.265°", dict(H=10.0, n_days=10, sig_D=0.02))
NEAR_D = (100, 300, 800, 2000)
CLIP = 1.0e6


def compute():
    """下絵の main() と同じ順番で乱数を引く"""
    rng = np.random.default_rng(SEED)
    steps = []
    for sid, name, kw in STEPS:
        C, th = run(0, rng, **kw)
        s = stats(C)
        steps.append(dict(id=sid, name=name, **s, samples=[round(float(v), 1) for v in np.clip(C, -CLIP, CLIP)],
                          theta_med=float(np.median(th)), kw={k: v for k, v in kw.items()}))
    C, th = run(0, rng, **TWIST[2])
    twist = dict(id=TWIST[0], name=TWIST[1], **stats(C))
    near_fine, near_coarse = [], []
    for d in NEAR_D:
        z = Z_S + d / C_TRUE * 360
        C, th = run(0, rng, H=10.0, n_days=10, blur=0.05, sig_D=0.02, D_base=d, z=z, z0=Z_S)
        near_fine.append(dict(d=d, name=f"  {d}km 離れた町", **stats(C), samples=[round(float(v), 1) for v in np.clip(C, -CLIP, CLIP)]))
    for d in NEAR_D:
        z = Z_S + d / C_TRUE * 360
        C, th = run(0, rng, D_base=d, z=z, z0=Z_S)
        near_coarse.append(dict(d=d, name=f"  {d}km 離れた町", **stats(C), samples=[round(float(v), 1) for v in np.clip(C, -CLIP, CLIP)]))
    no_err = D_GC * 360 / Z_A
    res = dict(
        slug=SLUG, n=N, seed=SEED,
        consts=dict(lat_s=LAT_S, lon_s=LON_S, lat_a=LAT_A, lon_a=LON_A, eps=EPS, c_true=C_TRUE, sun_half=SUN_HALF,
                    d_gc=D_GC, d_mer=D_MER, d_ew=D_EW, z_a=Z_A, z_s=Z_S, dlat=LAT_A - LAT_S,
                    no_err=no_err, no_err_pct=no_err / C_TRUE - 1, correct=D_MER * 360 / (LAT_A - LAT_S),
                    stadion_157=250000 * 0.1575, stadion_185=250000 * 0.185),
        steps=steps, twist=twist, near_fine=near_fine, near_coarse=near_coarse,
        breakdown=dict(before=breakdown(10.0, 0.015, 1, SUN_HALF, 0.10), after=breakdown(10.0, 0.015, 1, SUN_HALF, 0.02)),
        near_angle_100=100 / C_TRUE * 360,
    )
    return res


# ============================================================
# 1. 台本の数字を読む（モデルの照合用。場面の部分とは別に、文字だけ読む）
# ============================================================
NARR_PATH = ROOT / "publish" / SLUG / "narration_B.md"


def narration_text():
    """「## 0」より後の「- 」の行から、〔 〕と（ ）だけの行を除いた声の文を、章ごとに結ぶ"""
    txt = []
    on = False
    for raw in NARR_PATH.read_text(encoding="utf-8").splitlines():
        if re.match(r"##\s*0\s", raw):
            on = True
            continue
        if not on or not raw.startswith("- "):
            continue
        body = raw[2:].strip()
        if body.startswith("（") or body.startswith("〔"):
            continue
        body = re.sub(r"〔[^〕]*〕\s*$", "", body).strip()
        txt.append(body)
    return "\n".join(txt)


def _int(x):
    return int(math.floor(float(x) + 0.5))


def check(res):
    """照合。名前と OK/NG の一覧を返す。1つでも NG なら止める"""
    out = []

    def A(name, ok):
        out.append((name, bool(ok)))
    st = {s["id"]: s for s in res["steps"]}
    S = [st[k] for k in ("S1", "S2", "S3", "S4", "S5")]
    c = res["consts"]
    # ---- 下絵と1行ずつ突き合わせる ----
    cp = subprocess.run([sys.executable, "-X", "utf8", str(DRAFT)], capture_output=True, text=True, encoding="utf-8", cwd=str(ROOT))
    draft = [ln.rstrip() for ln in cp.stdout.splitlines()]
    A("下絵が最後まで走る（sims/chikyu-long.draft.py）", cp.returncode == 0 and len(draft) > 20)
    head = (f"大圏距離 {D_GC:.0f}km  南北成分 {D_MER:.0f}km  影の角度 {Z_A:.2f}°  シエネの太陽 {Z_S:.2f}°  緯度差 {LAT_A - LAT_S:.2f}°")
    A(f"下絵の1行目と同じ: {head}", head in draft)
    A(f"下絵: 誤差なしでエラトステネスのやり方 {c['no_err']:,.0f}km（{c['no_err_pct']:+.1%}）", f"誤差なしでエラトステネスのやり方: {c['no_err']:,.0f}km（{c['no_err_pct']:+.1%}）" in draft)
    A(f"下絵: 正しい置き方（南北の距離÷緯度差）{c['correct']:,.0f}km", f"  正しい置き方（南北の距離÷緯度差）: {c['correct']:,.0f}km" in draft)
    A(f"下絵: 史実の数字 157.5m {c['stadion_157']:,.0f}km・185m {c['stadion_185']:,.0f}km",
      f"  史実の数字 5,000スタディオン×50 = 250,000スタディオン → 157.5m: {c['stadion_157']:,.0f}km / 185m: {c['stadion_185']:,.0f}km" in draft)
    rows = [(s["name"], s) for s in S] + [(res["twist"]["name"], res["twist"])] + [(s["name"], s) for s in res["near_fine"]] + [(s["name"], s) for s in res["near_coarse"]]
    for name, s in rows:
        line = row_text(name, s)
        A(f"下絵と同じ行: {line.strip()}", line in draft)
    # ---- 梯子（段が進むと良くなる・単調） ----
    w10 = [s["w10"] for s in S]
    w5 = [s["w5"] for s in S]
    mad = [s["mad"] for s in S]
    A(f"±10%以内は段が進むたびに増える（単調）: {[round(v * 100, 1) for v in w10]}", all(a < b for a, b in zip(w10[:4], w10[1:4])) and w10[3] < w10[4] + 1e-12 and w10[0] < w10[1] < w10[2])
    A(f"±5%以内は 段1<段2<段3<段4<段5（単調）: {[round(v * 100, 1) for v in w5]}", all(a < b for a, b in zip(w5, w5[1:])))
    A(f"ずれの中央値は段が進むたびに小さくなる（単調）: {[round(v * 100, 1) for v in mad]}", all(a > b for a, b in zip(mad, mad[1:])))
    A("ひねり: 太陽のぼやけだけ残すと、段4とほぼ同じ（±5%以内の差 1ポイント以内）", abs(res["twist"]["w5"] - S[3]["w5"]) < 0.01)
    A("負の答えは段1〜5の1万回に1つもない（「測れない ×」は町が近いときだけ）", all(s["n_neg"] == 0 for s in S))
    # ---- 台本の数字 = data.json ----
    pc = lambda v: _int(v * 100)
    A(f"±10%の当たり: 段1 {pc(S[0]['w10'])}・段2 {pc(S[1]['w10'])}（台本 48・66）", (pc(S[0]["w10"]), pc(S[1]["w10"])) == (48, 66))
    A(f"段3の±10%は 99回を超える（{S[2]['w10'] * 100:.1f}%）・99.7", S[2]["w10"] > 0.99 and f"{S[2]['w10'] * 100:.1f}" == "99.7")
    A(f"±5%に数え直すと: 段3 {pc(S[2]['w5'])}（台本 84）・段4 {pc(S[3]['w5'])}（86）・段5 {pc(S[4]['w5'])}（95ほど）", (pc(S[2]["w5"]), pc(S[3]["w5"]), pc(S[4]["w5"])) == (84, 86, 95))
    A(f"ずれの中央値: 段1 {S[0]['mad']:.1%}（約10%）・段3 {S[2]['mad']:.1%}（約2%）・段4 {S[3]['mad']:.1%}（約2%）・段5 {S[4]['mad']:.1%}（1.8%）",
      (pc(S[0]["mad"]), pc(S[2]["mad"]), pc(S[3]["mad"]), f"{S[4]['mad'] * 100:.1f}") == (10, 2, 2, "1.8"))
    A(f"段1の1万回の中央値 {S[0]['med']:,.0f}km ＝ 台本の「4万600km」（100km単位）", _int(S[0]["med"] / 100) * 100 == 40600)
    A(f"段1の中央値は本当の値に近い（{S[0]['med'] / C_TRUE - 1:+.1%}）のに、1回ごとはばらつく（1〜9割 {S[0]['p10']:,.0f}〜{S[0]['p90']:,.0f}km が本当の値±20%の幅）",
      abs(S[0]["med"] / C_TRUE - 1) < 0.02 and (S[0]["p90"] - S[0]["p10"]) / C_TRUE > 0.3)
    A("距離のぶれ 10%→2% で段2→3が一気に伸びる（+34ポイント以上）・棒を10mにした段1→2は +20ポイント未満",
      S[2]["w10"] - S[1]["w10"] > 0.30 and S[1]["w10"] - S[0]["w10"] < 0.20)
    bd = res["breakdown"]["before"]
    A(f"ぶれの内訳（段2の条件・1つずつ）: 距離 {bd['distance']:.1%}・影の読み取り {bd['reading']:.1%}・影の先の癖 {bd['habit']:.1%} → 距離が最大", bd["distance"] > 3 * max(bd["reading"], bd["habit"]))
    # ---- 地球一周の式・考え方 ----
    A("360 ÷ 7.2 ＝ 50 ／ 800km × 50 ＝ 4万km", abs(360 / 7.2 - 50) < 1e-9 and 800 * 50 == 40000)
    A(f"2つの町: 大圏距離 {c['d_gc']:.0f}km・南北の道のり {c['d_mer']:.0f}km → 台本の「約800km」は両方の丸め（100km単位）", _int(c["d_gc"] / 100) * 100 == 800 and _int(c["d_mer"] / 100) * 100 == 800)
    A(f"台本「844km」「790km」＝ {c['d_gc']:.0f}・{c['d_mer']:.0f}／東西にずれた分 {c['d_ew']:.0f}km（図のための三平方）", f"{c['d_gc']:.0f}" == "844" and f"{c['d_mer']:.0f}" == "790" and abs(math.hypot(c["d_mer"], c["d_ew"]) - c["d_gc"]) < 1e-6)
    A(f"エラトステネスの考え方（誤差なし）{c['no_err']:,.0f}km ＝ 台本の「4万632km」・本当の値より {c['no_err_pct']:+.1%}（台本 1.6%）", f"{_int(c['no_err']):,}" == "40,632" and f"{c['no_err_pct'] * 100:.1f}" == "1.6")
    A(f"正しい計算（南北の道のり÷緯度の差×360）{c['correct']:,.0f}km ＝ 40,008km（約4万km）", f"{c['correct']:,.0f}" == "40,008")
    A(f"シエネの太陽は真上から {c['z_s']:.2f}° ≒ 台本の「0.4度ほど」・角度の差の向き: シエネの角度を0にして計算すると北の町の角度が {c['z_a']:.2f}° と大きく読まれる（本当は {c['dlat']:.2f}°）→ 一周は小さく出る",
      f"{c['z_s']:.1f}" == "0.4" and c["z_a"] > c["dlat"])
    A(f"844kmを使うと距離が長すぎて一周は大きく出る（844/790 ＝ {c['d_gc'] / c['d_mer']:.3f}）・角度の効き（{c['dlat'] / c['z_a']:.3f}）と打ち消し合う（積 {c['d_gc'] / c['d_mer'] * c['dlat'] / c['z_a']:.3f} ≒ 1.016）",
      c["d_gc"] / c["d_mer"] > 1 and c["dlat"] / c["z_a"] < 1 and abs(c["d_gc"] / c["d_mer"] * c["dlat"] / c["z_a"] - (1 + c["no_err_pct"])) < 1e-9)
    # ---- スタディオン ----
    A(f"25万スタディオン × 157.5m ＝ {c['stadion_157']:,.0f}km ≒ 約3万9千km（本当の値より {c['stadion_157'] / C_TRUE - 1:+.1%}）", f"{_int(c['stadion_157'] / 1000)}" == "39")
    A(f"25万スタディオン × 185m ＝ {c['stadion_185']:,.0f}km ≒ 約4万6千km（本当の値より大きい）", f"{_int(c['stadion_185'] / 1000)}" == "46" and c["stadion_185"] > C_TRUE)
    A("スタディオンの2つの値は、本当の値をはさむ（3万9千 < 4万 < 4万6千）", c["stadion_157"] < C_TRUE < c["stadion_185"])
    # ---- 町が近いとき ----
    nf = {d["d"]: d for d in res["near_fine"]}
    nc = {d["d"]: d for d in res["near_coarse"]}
    A(f"町が近いとき（段1の測り方）の±10%は、町が遠いほど増える（単調）: {[round(nc[d]['w10'] * 100, 1) for d in NEAR_D]}", all(nc[a]["w10"] < nc[b]["w10"] for a, b in zip(NEAR_D, NEAR_D[1:])))
    A(f"町が近いとき（段5の測り方）の±10%: {[round(nf[d]['w10'] * 100, 1) for d in NEAR_D]}・±5%は単調に増える {[round(nf[d]['w5'] * 100, 1) for d in NEAR_D]}",
      nf[100]["w10"] < nf[300]["w10"] <= nf[800]["w10"] and all(nf[a]["w5"] < nf[b]["w5"] for a, b in zip(NEAR_D, NEAR_D[1:])))
    A(f"100kmの町: 雑な測り方は±10%に {nc[100]['w10'] * 100:.1f}%（台本「100回に8回ほど」）・丁寧な測り方は {nf[100]['w10'] * 100:.1f}%（台本「96回」）",
      abs(nc[100]["w10"] * 100 - 8) < 1.0 and pc(nf[100]["w10"]) == 96)
    A(f"800kmの町（雑な測り方・別の1万回）は {nc[800]['w10'] * 100:.2f}% で、段1（第1章の町・{S[0]['w10'] * 100:.2f}%）と1ポイント以内。第5章の「100回に48回」「棒800km」は第1章の値（段1）を使う",
      pc(S[0]["w10"]) == 48 and abs(nc[800]["w10"] - S[0]["w10"]) < 0.01)
    A(f"100kmだと影の角度の差は {res['near_angle_100']:.2f}° ＝ 1度に届かない（台本）", res["near_angle_100"] < 1.0)
    A(f"100kmの雑な測り方は答えが負になる回がある（{nc[100]['n_neg']}回 ＝ 絵では「測れない ×」）・丁寧な測り方では 0回（{nf[100]['n_neg']}）", nc[100]["n_neg"] > 0 and nf[100]["n_neg"] == 0)
    A("data.json の1万回: 各段の samples は 1万個", all(len(s["samples"]) == N for s in S) and all(len(s["samples"]) == N for s in res["near_fine"] + res["near_coarse"]))
    # ---- 台本（文字）に書いてある数字が data.json と合っている ----
    nt = narration_text()
    want = [
        f"100回に{pc(S[0]['w10'])}回でした", f"100回に{pc(S[1]['w10'])}回でした", "100回のうち、99回を超えます", f"100回に{pc(S[2]['w5'])}回です",
        f"100回に{pc(S[3]['w5'])}回", f"100回に{pc(S[4]['w5'])}回ほどでした", "4万600km", "約2%から、1.8%に下がりました", "中央値は、約2%でした", "約10%でした",
        "4万632km", "1.6%だけ大きい", "844kmです", "790kmです", "約800km", "800kmの50倍で、4万km", "360を7.2で割ると、50", "7.2度",
        "100回に8回ほどです", "100回に96回でした", "100回に48回でした", "25万スタディオン", "25万2千スタディオン", "157.5メートル", "約3万9千km",
        "185メートル", "約4万6千km", "0.4度ほど", "決着していません", "100kmにします",
    ]
    miss = [w for w in want if w not in nt]
    A(f"台本（narration_B.md）に、data.json から出る言葉が{len(want)}個そろっている: 足りないもの {miss}", not miss)
    A("台本: 本文に「誤差1%」「ベマティスト」「らくだ」「井戸」を書いていない（言わない決まり）", not any(w in nt for w in ("誤差1%", "ベマティスト", "らくだ", "井戸")))
    bad = [name for name, ok in out if not ok]
    for name, ok in out:
        print(("  OK  " if ok else "  NG  ") + name)
    if bad:
        raise SystemExit(f"照合に失敗: {len(bad)}件")
    print(f"照合 {len(out)} 件 OK")
    return out


def write_numbers(res, checks):
    c = res["consts"]
    S = res["steps"]
    rows = ["# 数字（棒1本で地球の大きさ ロング・sims/chikyu-long.py --numbers が書く。手で直さない）", "",
            f"{res['n']:,} 回・乱数の種 {res['seed']}・本当の値（北極・南極を回る一周）{c['c_true']:,.0f}km・計算は sims/chikyu-long.draft.py と同じ（出力を1行ずつ突き合わせ済み）", "",
            "## 梯子（当たり＝本当の値から ±10% 以内／後半は ±5% 以内。ずれの中央値＝ずれ（割合）の中央値）", "",
            "| 段 | 中央値 | 1割〜9割 | ±10%以内 | ±5%以内 | ずれの中央値 |", "|---|---|---|---|---|---|"]
    for s in S:
        rows.append(f"| {s['name']} | {s['med']:,.0f} km | {s['p10']:,.0f}〜{s['p90']:,.0f} km | {s['w10']:.1%}（{s['n10']:,}回） | {s['w5']:.1%}（{s['n5']:,}回） | {s['mad']:.1%} |")
    t = res["twist"]
    rows.append(f"| ひねり（ぼやけだけ残す） | {t['med']:,.0f} km | {t['p10']:,.0f}〜{t['p90']:,.0f} km | {t['w10']:.1%} | {t['w5']:.1%} | {t['mad']:.1%} |")
    for key, title in (("near_fine", "町が近いとき・段5の測り方（棒10m・10日・影の先くっきり・距離±2%）"), ("near_coarse", "町が近いとき・段1の測り方（棒1m・目で読む・距離±10%）")):
        rows += ["", f"## {title}", "", "| 町の距離 | 中央値 | 1割〜9割 | ±10%以内 | ±5%以内 | ずれの中央値 | 答えが負（測れない） |", "|---|---|---|---|---|---|---|"]
        for d in res[key]:
            rows.append(f"| {d['d']:,} km | {d['med']:,.0f} km | {d['p10']:,.0f}〜{d['p90']:,.0f} km | {d['w10']:.1%} | {d['w5']:.1%} | {d['mad']:.1%} | {d['n_neg']:,}回 |")
    rows += ["", "## 考え方（誤差なし）", "",
             f"- 2つの町: 大圏距離 {c['d_gc']:.0f} km／南北の道のり {c['d_mer']:.0f} km／東西にずれた分 約{c['d_ew']:.0f} km（図用）／緯度の差 {c['dlat']:.2f}°",
             f"- 北の町の影の角度（当時の地軸の傾き {c['eps']}°）{c['z_a']:.2f}°／南の町の太陽は真上から {c['z_s']:.2f}°",
             f"- エラトステネスの考え方（距離×360÷影の角度・南の町の角度は0）: {c['no_err']:,.0f} km（本当の値より {c['no_err_pct']:+.1%}）",
             f"- 正しい計算（南北の道のり÷緯度の差×360）: {c['correct']:,.0f} km",
             f"- スタディオン: 25万 × 157.5 m ＝ {c['stadion_157']:,.0f} km／25万 × 185 m ＝ {c['stadion_185']:,.0f} km",
             f"- ぶれの内訳（絵の棒の長さだけに使う）: 段2の条件で 距離 {res['breakdown']['before']['distance']:.1%}・影の読み取り {res['breakdown']['before']['reading']:.1%}・影の先の癖 {res['breakdown']['before']['habit']:.1%}",
             "", "## 照合", ""] + [f"- {'OK' if ok else 'NG'} {name}" for name, ok in checks]
    rows += ["", f"照合 {len(checks)} 件 OK"]
    (OUT / "numbers.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("numbers.md:", OUT / "numbers.md")


def save(res):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print("data.json:", OUT / "data.json")


def load():
    return json.loads((OUT / "data.json").read_text(encoding="utf-8"))


_MODEL_CLI = any(a in sys.argv for a in ("--check", "--numbers"))
if __name__ == "__main__" and _MODEL_CLI:
    if "--numbers" in sys.argv:
        print("計算します…", flush=True)
        _res = compute()
        save(_res)
        _res = load()
    else:
        _res = load()
    _chk = check(_res)
    if "--numbers" in sys.argv:
        write_numbers(_res, _chk)
    raise SystemExit


# ==== 場面 ====

# ####################################################################################################
# ここから下は場面（描画・音・照合・書き出し）。inoh-long.py と同じ並び・同じ部品（見開きノート・付せん・章カード・終了画面・照合）。
# 台本: publish/chikyu-long/narration_B.md の「## 0」より後の「- 」の行を、そのまま読み込む（〔 〕は画面の絵の指示、（無音…）は声のない区間）。
#   台本の言葉が少し変わっても流れるよう、場面の合図は「文の一部（手がかり）」で探す（見つからなければ止まる）。
# 部品: engine/longkit.py（LadderPanel の「＋」「↓」・枠は声の0.5秒前・OpeningTeaser・GridPanel・scan_frames・text_box_overlaps・visual_lag・value_spoilers・min_text_size・small）。
#
# 使い方
#   python -X utf8 sims/chikyu-long.py --scenecheck --fake-voice    場面の照合だけ（音声なし・長さは見積もり）
#   python -X utf8 sims/chikyu-long.py --stills --fake-voice        要所の静止画と sheet_480.png（out/chikyu-long/stills_preview/）。--at 0,2.5,5 なら指定した秒だけ（scene_work/）
#   python -X utf8 sims/chikyu-long.py --wraps --fake-voice         字幕の折り返しを全部表示
#   python -X utf8 sims/chikyu-long.py --readings --fake-voice      読みの確認（scene_work/readings.log）
#   python -X utf8 sims/chikyu-long.py --docs --fake-voice          文字起こし・チャプター（scene_work/）
#   python -X utf8 sims/chikyu-long.py --anchors --fake-voice       場面の合図の時刻
#   python -X utf8 sims/chikyu-long.py --preview                    960×540 の確認用動画（AivisSpeech の音声）
#   （本番の書き出し=AivisSpeech の音声つき は、この段階ではまだしない）
# ####################################################################################################
import re as _re
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine import longkit as lk
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
# 台本の読み込み（narration_B.md の「## 0」より後の「- 」の行。文言は一字も変えない）
#   「- （無音 3秒・…）」＝声のない区間（Gap） ／ 「- （…）」「- 〔…〕」だけの行＝画面の指示（声にしない）
#   行の終わりの〔…〕＝その文のときの画面の絵（声にしない）
# ============================================================
GAP_FAST = 3.0                                   # 「（無音・早回し。…）」に秒数が書いていないときの長さ（4秒以内）


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
CARD_TITLES = [t_.replace("　", "\n") for t_ in CH_TITLES]       # 章カードに出す題（全角空白で2行に）
LINES = {}                         # 文の id -> (章, 文)
LINE_NOTE = {}                     # 文の id -> 〔画面の絵〕
GAP_NOTE = {}                      # 無音の id -> 注
GAP_SEC = {}
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
    res = []
    for p in out:                                  # それでも2行に収まらない1文だけ、真ん中に近い「、」で分ける（文言は変えない）
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
                for j, part in enumerate(parts):          # 字幕が2行に収まらない文は、文言を変えずに「。」で2つの Line に分ける
                    lid = f"c{n}_{k}"
                    k += 1
                    LINES[lid] = (n, part)
                    LINE_NOTE[lid] = note_ if j == 0 else ""
                    last = li == len(lines) and j == len(parts) - 1
                    out.append(lf.Line(lid, part, pause=0.3 if n == 0 else (0.6 if last else 0.35), speed=SPEED_V))      # 0章は、どの文のあとも約0.3秒
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
# 小さな道具（inoh-long・okehazama-long と同じ）
# ============================================================
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
LCX = 492                                            # 左ページの中央
PENCIL_T = "#454d62"                                 # 補足の文字
BLUE = "#3a73c8"
GREEN = "#3f9a6a"
ORANGE = "#e0892a"
BROWN = "#7a4b25"                                    # 棒
SKY = "#f5c542"                                      # 太陽
EARTH_F = "#d9e8d0"                                  # 地球の断面（うすい緑）
EARTH_L = "#6b8f6b"


def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


def window(t, t0, t1, fi=0.3, fo=0.3):
    """t0〜t1 の間だけ 1（出入りのフェード付き）"""
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


# ============================================================
# 準備（データ・時間割）
# ============================================================
lf.use()
RES = load()
_syn = _fake_synth if FAKE else _voice_synth
tl = lf.Timeline(_breathe(_items()), VOICE_DIR, lead=0.5, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


def ease_in_out(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ---- 場面の合図: 文の一部（手がかり）から文の id を探す。台本が変わって見つからなくなったら止める ----
ANCH = {
    # 0 冒頭
    "c0_q": (0, "2200年前の人は"), "c0_era": (0, "エラトステネスという学者は"), "c0_ans": (0, "その答えは"), "c0_10k": (0, "1万回やり直します"),
    "c0_first": (0, "先に言うと"), "c0_dist": (0, "ただし、答えを大きく左右"), "c0_cond": (0, "条件をそろえます"),
    "c0_ge": (0, "測るのは、夏至の正午"), "c0_south": (0, "南の町シエネ"), "c0_north": (0, "同じ時刻、エジプトの北の町アレクサンドリア"),
    "c0_stick": (0, "棒は立っています"), "c0_tilt": (0, "影の角度と呼びます"), "c0_72": (0, "7.2度にあたると"), "c0_360": (0, "円は一周で、360度"),
    "c0_q72": (0, "何分の1でしょう"), "c0_50": (0, "360を7.2で割ると"), "c0_why": (0, "なぜ地球の大きさが出る"), "c0_par": (0, "光は、どこでも同じ向き"),
    "c0_ext": (0, "まっすぐ下に伸ばすと"), "c0_sov": (0, "南の町の棒は、光の向きとほぼ重なります"), "c0_nov": (0, "北の町の棒は、光から"),
    "c0_cen": (0, "地球の中心で、2本の棒"), "c0_arc": (0, "50分の1なら"), "c0_800": (0, "約800km離れています"), "c0_x50": (0, "800kmの50倍"),
    "c0_move": (0, "ひとつずつ足していきます"), "c0_next": (0, "ひとつずつ足していきます"),
    # 1 そのまま・棒を長く
    "c1_0": (1, "この章では"), "c1_base": (1, "当たりの基準は"), "c1_true": (1, "本当の値は、約4万km"), "c1_stick": (1, "棒は、1mです"),
    "c1_read": (1, "1.5cmほどぶれる"), "c1_blur": (1, "影の先は、ぼやけます"), "c1_dist": (1, "10%ほどぶれる"), "c1_med": (1, "中央値は、4万600km"),
    "c1_wide": (1, "大きくばらつきます"), "c1_hit": (1, "100回に48回"), "c1_add": (1, "棒を10mにすることを足すと"), "c1_x10": (1, "棒が10倍なら"),
    "c1_tenth": (1, "割合で10分の1"), "c1_hit2": (1, "100回に66回でした"), "c1_end": (1, "分かったことです"),
    # 2 距離
    "c2_prev": (2, "前の章では"), "c2_0": (2, "この章では"), "c2_dist": (2, "距離のぶれが"), "c2_2pct": (2, "2%に縮まった"),
    "c2_add": (2, "距離をきちんと測ることを足すと"), "c2_99": (2, "99回を超えます"), "c2_prop": (2, "距離に比例して"),
    "c2_1wari": (2, "1割ずれたら"), "c2_break": (2, "距離が1割ずれたら"), "c2_strict": (2, "基準を厳しくします"), "c2_5pct": (2, "5%以内で見ます"),
    "c2_84": (2, "100回に84回"), "c2_zure": (2, "答えと本当の値との差"), "c2_mid": (2, "中央値は"),
    "c2_res": (2, "棒1mのときは"), "c2_end": (2, "分かったことです"),
    # 3 平均・くっきり
    "c3_0": (3, "この章では"), "c3_add10": (3, "10日測って"), "c3_cal": (3, "夏至に近い10日間"), "c3_avg": (3, "平均すると、小さくなります"),
    "c3_86": (3, "100回に86回"), "c3_same": (3, "ほとんど変わりません"), "c3_habit": (3, "どこで読むかに、癖"),
    "c3_always": (3, "毎日同じなので"), "c3_add2": (3, "影の先をくっきり読むことを足すと"), "c3_tool": (3, "くっきり読める道具"), "c3_95": (3, "100回に95回ほど"),
    "c3_mad": (3, "1.8%に下がりました"), "c3_end": (3, "分かったことです"),
    # 4 考え方
    "c4_0": (4, "この章では"), "c4_zero": (4, "測りまちがいを、すべてなくします"), "c4_632": (4, "4万632km"), "c4_16": (4, "1.6%だけ大きい"), "c4_lat": (4, "緯度とは"),
    "c4_diff": (4, "緯度の差が"), "c4_cor": (4, "南北の道のりで計算すると"), "c4_same": (4, "ほぼ同じです"), "c4_why": (4, "ほぼ当たるのでしょうか"), "c4_cancel": (4, "2つあって、打ち消し合う"),
    "c4_sun": (4, "太陽の向きです"), "c4_0deg": (4, "0度として計算"), "c4_big": (4, "そのぶん大きく読まれます"), "c4_small": (4, "地球一周は、小さく出ます"),
    "c4_pos": (4, "町の並びです"), "c4_844": (4, "844kmです"), "c4_790": (4, "790kmです"), "c4_844b": (4, "844を使うと"), "c4_end": (4, "分かったことです"),
    # 5 近い町
    "c5_0": (5, "この章では"), "c5_100": (5, "100kmにします"), "c5_crit": (5, "10%以内で見ます"), "c5_8": (5, "100回に8回ほど"), "c5_800": (5, "800kmなら"),
    "c5_48": (5, "100回に48回でした"), "c5_why": (5, "埋もれるからです"), "c5_fine": (5, "いちばん丁寧な測り方なら"), "c5_desc": (5, "全部使います"), "c5_96": (5, "100回に96回"),
    "c5_end": (5, "分かったことです"),
    # 6 スタディオン
    "c6_0": (6, "この章では"), "c6_def": (6, "古代ギリシャの"), "c6_25": (6, "地球一周は、25万スタディオン"), "c6_252": (6, "25万2千スタディオン"),
    "c6_which": (6, "どちらが元の数字か"), "c6_len": (6, "決着していません"), "c6_157": (6, "157.5メートル"), "c6_185": (6, "185メートルとすると"), "c6_end": (6, "分かったことです"),
    # 7 まとめ
    "c7_0": (7, "距離をきちんと測れれば"), "c7_1": (7, "距離をきちんと測れれば"), "c7_2": (7, "距離をきちんと測れれば"), "c7_3": (7, "大事なのは"),
    "c7_4": (7, "あなたなら"), "c7_5": (7, "数字は、この動画の条件"), "c7_ch": (7, "このチャンネルでは"), "c7_sub": (7, "よければ"),
}


def _find(n, sub):
    hits = [lid for lid, (cn, txt) in LINES.items() if cn == n and sub in txt]
    return hits[0] if len(hits) == 1 else None


ID = {k: _find(*v) for k, v in ANCH.items()}
_bad = [f"{k}（第{ANCH[k][0]}章「{ANCH[k][1]}」）" for k, v in ID.items() if v is None]
if _bad:
    raise SystemExit("台本の手がかりが1件だけ見つかりません（0件か2件以上）。narration_B.md が変わったら ANCH を直してください: " + "、".join(_bad))


def Sk(k, f=0.0):
    return S(ID[k]) + f * dur(ID[k])


def Ek(k):
    return E(ID[k])


def Dk(k):
    return dur(ID[k])


# ---- データ ----
STEP = {s["id"]: s for s in RES["steps"]}
SMP = {k: np.array(STEP[k]["samples"]) for k in STEP}
NEAR_F = {d["d"]: d for d in RES["near_fine"]}
NEAR_C = {d["d"]: d for d in RES["near_coarse"]}
C_T = RES["consts"]["c_true"]
CONST = RES["consts"]


def pc(v):
    return f"{ihalf(v * 100)}%"


# ============================================================
# 幾何（地球の断面図・棒・影・平行な光）。角は「上」を 0 として右（北）を正にした地球の中心角。画面は y が下向き
# ============================================================
DRAW_HALF = math.radians(15.0)                       # 描く角度の半分（2本の棒の間は30度に大きく描く。本当は7.2度）
PHI_S, PHI_N = -DRAW_HALF, DRAW_HALF                 # 南の町・北の町の位置
VA = (492.0, 1020.0, 640.0)                          # 冒頭の見え方（地平線が大きい）
VB = (492.0, 595.0, 285.0)                           # 断面図
STICK_A, STICK_B = 245.0, 105.0                      # 棒の長さ（画面の px）


def U(phi):
    """地球の中心から見た向き phi の外向きの単位ベクトル"""
    return (math.sin(phi), -math.cos(phi))


def cpt(V, phi, r):
    return (V[0] + r * math.sin(phi), V[1] - r * math.cos(phi))


def sun_phi_a(t):
    """冒頭の太陽の向き: 北の棒の真上 → 南の棒の真上へ（最初から動く）。3.6秒で止まる"""
    u = clamp01(t / 3.6)
    return lerp(PHI_N, PHI_S, 1 - (1 - u) ** 2)


def ray_dir(phi_sun):
    """光の進む向き（太陽の向きの逆）"""
    u = U(phi_sun)
    return (-u[0], -u[1])


def ray_hit(V, tip, phi_sun):
    """棒の先を通る光が地面（円）に当たる点。当たらなければ None"""
    d = ray_dir(phi_sun)
    px, py = tip[0] - V[0], tip[1] - V[1]
    b = px * d[0] + py * d[1]
    c = px * px + py * py - V[2] ** 2
    disc = b * b - c
    if disc < 0:
        return None
    s = -b - math.sqrt(disc)
    return (tip[0] + s * d[0], tip[1] + s * d[1])


def phi_of(V, p):
    return math.atan2(p[0] - V[0], -(p[1] - V[1]))


def geometry_checks():
    """幾何の照合: 光は南の棒（の延長）と厳密に平行・北の棒との角 ＝ 2本の棒の中心角（同位角）・南の棒の影は0"""
    out = {}
    d = ray_dir(PHI_S)
    us = U(PHI_S)
    out["cross"] = abs(d[0] * us[1] - d[1] * us[0])                                   # 光と南の棒の外積（0 なら平行）
    un = U(PHI_N)
    ang_tip = math.acos(max(-1.0, min(1.0, -(d[0] * un[0] + d[1] * un[1]))))         # 北の棒と太陽の向きのあいだの角
    ang_cen = math.acos(max(-1.0, min(1.0, un[0] * us[0] + un[1] * us[1])))           # 中心角
    out["ang_tip"], out["ang_cen"] = math.degrees(ang_tip), math.degrees(ang_cen)
    tipS = cpt(VB, PHI_S, VB[2] + STICK_B)
    hs = ray_hit(VB, tipS, PHI_S)
    baseS = cpt(VB, PHI_S, VB[2])
    out["shadow_s"] = math.hypot(hs[0] - baseS[0], hs[1] - baseS[1]) if hs else None
    tipN = cpt(VB, PHI_N, VB[2] + STICK_B)
    hn = ray_hit(VB, tipN, PHI_S)
    baseN = cpt(VB, PHI_N, VB[2])
    out["shadow_n"] = math.hypot(hn[0] - baseN[0], hn[1] - baseN[1]) if hn else None
    # 冒頭: 最後のコマで南の影 0・北の影 > 0／最初のコマで北の影 0・南の影 > 0
    for key, tt in (("a0", 0.0), ("a1", 6.0)):
        ps = sun_phi_a(tt)
        r = {}
        for nm, ph in (("s", PHI_S), ("n", PHI_N)):
            tip = cpt(VA, ph, VA[2] + STICK_A)
            h = ray_hit(VA, tip, ps)
            base = cpt(VA, ph, VA[2])
            r[nm] = math.hypot(h[0] - base[0], h[1] - base[1]) if h else None
        out[key] = r
    return out


def earth_body(ctx, V, a=1.0, fill_col=EARTH_F):
    ctx.arc(V[0], V[1], V[2], 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(fill_col, 0.95 * a))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(EARTH_L, a))
    ctx.set_line_width(7)
    ctx.stroke()


def arc_on(ctx, V, p0, p1, r, col, w, a=1.0, cap=cairo.LINE_CAP_ROUND):
    """地球の中心角 p0 から p1 までの円弧（半径 r）"""
    if abs(p1 - p0) < 1e-9:
        return
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cap)
    if p1 > p0:
        ctx.arc(V[0], V[1], r, p0 - math.pi / 2, p1 - math.pi / 2)
    else:
        ctx.arc_negative(V[0], V[1], r, p0 - math.pi / 2, p1 - math.pi / 2)
    ctx.stroke()


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
    """tip に向かう矢じり。d は進む向きの単位ベクトル"""
    ang = math.atan2(d[1], d[0])
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for s_ in (-1, 1):
        ctx.move_to(tip[0] - size * math.cos(ang + s_ * 0.45), tip[1] - size * math.sin(ang + s_ * 0.45))
        ctx.line_to(*tip)
    ctx.stroke()


def arrow2(ctx, p, q, col, w=6.0, a=1.0, both=False, head=22.0):
    line2(ctx, p, q, col, w, a)
    d = (q[0] - p[0], q[1] - p[1])
    n = math.hypot(*d) or 1.0
    d = (d[0] / n, d[1] / n)
    arrowhead(ctx, q, d, col, head, a, w)
    if both:
        arrowhead(ctx, p, (-d[0], -d[1]), col, head, a, w)


def sun_disc(ctx, x, y, r=38, a=1.0):
    ctx.set_source_rgba(*hexrgb(SKY, 0.30 * a))
    ctx.arc(x, y, r * 1.55, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(SKY, a))
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#c98a10", a))
    ctx.set_line_width(4)
    ctx.arc(x, y, r, 0, 2 * math.pi)
    ctx.stroke()


def parallel_rays(ctx, V, phi_sun, offs, a=1.0, col="#e3a21a", w=5.0, y_top=150.0, hl=None):
    """太陽の向き phi_sun に平行な光の線（中心を通る線から offs だけ横にずらしたもの）。円に当たるところまで。hl={offs: 色}"""
    d = ray_dir(phi_sun)
    n = (math.cos(phi_sun), math.sin(phi_sun))
    for off in offs:
        if abs(off) >= V[2] - 1:
            continue
        half = math.sqrt(V[2] ** 2 - off ** 2)
        Q = (V[0] + n[0] * off, V[1] + n[1] * off)
        hit = (Q[0] - d[0] * half, Q[1] - d[1] * half)
        s0 = (hit[1] - y_top) / d[1]
        start = (hit[0] - d[0] * s0, hit[1] - d[1] * s0)
        c_ = (hl or {}).get(off, col)
        line2(ctx, start, hit, c_, w, a * 0.9)
        arrowhead(ctx, hit, d, c_, 20.0, a * 0.9, w)


def ray_offset_through(V, phi_sun, pt):
    n = (math.cos(phi_sun), math.sin(phi_sun))
    return (pt[0] - V[0]) * n[0] + (pt[1] - V[1]) * n[1]


def stick_and_shadow(ctx, V, phi_stick, phi_sun, h, col=BROWN, a=1.0, w=13.0, shadow=True):
    base = cpt(V, phi_stick, V[2])
    tip = cpt(V, phi_stick, V[2] + h)
    if shadow:
        hit = ray_hit(V, tip, phi_sun)
        if hit is not None:
            p1 = phi_of(V, hit)
            arc_on(ctx, V, phi_stick, p1, V[2] + 2, "#2d3548", 11.0, 0.85 * a, cap=cairo.LINE_CAP_BUTT)
    line2(ctx, base, tip, col, w, a)
    return base, tip


# ============================================================
# 0章 左ページ
# ============================================================
def clip_left(ctx):
    ctx.rectangle(45, 36, 890, 900)
    ctx.clip()


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


def L_earthA(ctx, t):
    """冒頭〜条件: 丸い地球の弧に2本の棒。0秒目から、片方の影が消え、もう片方の影が伸びる"""
    V = VA
    ps = sun_phi_a(t)
    earth_body(ctx, V)
    sx, sy = V[0] + ((V[1] - 105.0) / math.cos(ps)) * math.sin(ps), 105.0
    offS = ray_offset_through(V, ps, cpt(V, PHI_S, V[2] + STICK_A))
    offN = ray_offset_through(V, ps, cpt(V, PHI_N, V[2] + STICK_A))
    parallel_rays(ctx, V, ps, [-0.55 * V[2], -0.28 * V[2], 0.0, 0.28 * V[2], 0.55 * V[2], offS, offN], y_top=135.0)
    # 町と町のあいだの線（エラトステネスのくだりで引く）
    pr = clamp01((t - Sk("c0_era", 0.25)) / 1.0)
    if pr > 0:
        arc_on(ctx, V, PHI_S, lerp(PHI_S, PHI_N, pr), V[2] - 3, ORANGE, 9.0, 1.0)
    stick_and_shadow(ctx, V, PHI_S, ps, STICK_A)
    stick_and_shadow(ctx, V, PHI_N, ps, STICK_A)
    sun_disc(ctx, sx, sy)
    # 札
    bS, bN = cpt(V, PHI_S, V[2]), cpt(V, PHI_N, V[2])
    a_t = fade(t, Sk("c0_era", 0.25), 0.4)
    label(ctx, "南の町", bS[0], 470, 48, INK, a_t)
    label(ctx, "北の町", bN[0], 470, 48, INK, a_t)
    if t > Sk("c0_dist", 0.1):
        a_d = fade(t, Sk("c0_dist", 0.15), 0.4)
        pen_circle(ctx, V[0], V[1] - V[2] - 2, 330, 62, RED, seed=3, width=7, progress=clamp01((t - Sk("c0_dist", 0.15)) / 0.8), alpha=a_d)
        label(ctx, "2つの町の距離", V[0], 600, 52, RED, a_d)
    a_ge = fade(t, Sk("c0_ge", 0.1), 0.4)
    label(ctx, "夏至の正午", 520, 105, 48, INK, a_ge)
    label(ctx, "影なし", bS[0], 540, 46, BLUE, fade(t, Sk("c0_south", 0.55), 0.4))
    label(ctx, "影が伸びる", bN[0], 540, 46, ORANGE, fade(t, Sk("c0_north", 0.5), 0.4))


def L_ang(ctx, t):
    """棒1本と斜めの光だけの図。かたむきの角＝影の角度＝7.2度"""
    gy = 700.0
    bx = 420.0
    h = 300.0
    th = math.radians(30.0)                                  # 大きく描く（本当は7.2度）
    tip = (bx, gy - h)
    ray_end = (tip[0] - 380 * math.sin(th), tip[1] - 380 * math.cos(th))
    sh = (bx + h * math.tan(th), gy)
    line2(ctx, (100, gy), (880, gy), EARTH_L, 7)
    line2(ctx, (bx, gy), sh, "#2d3548", 13, 0.85, cap=cairo.LINE_CAP_BUTT)
    a_r = fade(t, Sk("c0_stick", 0.35), 0.5)
    line2(ctx, ray_end, sh, "#e3a21a", 6, 0.9 * a_r)
    arrowhead(ctx, sh, (math.sin(th), math.cos(th)), "#e3a21a", 22, 0.9 * a_r, 6)
    sun_disc(ctx, ray_end[0] - 22, ray_end[1] - 14, 36, a_r)
    line2(ctx, (bx, gy), tip, BROWN, 15)
    line2(ctx, tip, (bx, tip[1] - 150), "#9aa3b5", 4, 0.9, dash=[10, 9])
    # かたむきの角
    a_c = fade(t, Sk("c0_stick", 0.6), 0.4)
    ctx.set_source_rgba(*hexrgb(RED, a_c))
    ctx.set_line_width(7)
    ctx.arc_negative(tip[0], tip[1], 105, -math.pi / 2, -math.pi / 2 - th)
    ctx.stroke()
    label(ctx, "棒", bx - 64, gy - h * 0.45, 48, INK, fade(t, Sk("c0_stick", 0.1), 0.3))
    label(ctx, "影", (bx + sh[0]) / 2, gy + 56, 48, INK, fade(t, Sk("c0_stick", 0.3), 0.3))
    a_t = fade(t, Sk("c0_tilt", 0.25), 0.4)
    arrow2(ctx, (tip[0] + 180, tip[1] - 150), (tip[0] + 22, tip[1] - 118 + 20), RED, 4, a_t * 0.9)
    label(ctx, "影の角度", tip[0] + 270, tip[1] - 160, 52, RED, a_t)
    label(ctx, "＝ 7.2度", tip[0] + 270, tip[1] - 100, 52, RED, fade(t, Sk("c0_72", 0.5), 0.4))
    label(ctx, "角度は大きく描いてあります", 492, 835, 40, PENCIL_T, fade(t, Sk("c0_tilt", 0.1), 0.4))


def L_circ(ctx, t):
    """円は360度 → 7.2度は何分の1？ → 50に分けた図"""
    cx, cy, r = 492.0, 480.0, 245.0
    a_c = fade(t, Sk("c0_360", 0.0), 0.3)
    ctx.set_source_rgba(1, 1, 1, 0.55 * a_c)
    ctx.arc(cx, cy, r, 0, 2 * math.pi)
    ctx.fill()
    pr = clamp01((t - Sk("c0_360", 0.05)) / 1.4)
    ctx.set_source_rgba(*hexrgb(INK, a_c))
    ctx.set_line_width(8)
    ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + 2 * math.pi * pr)
    ctx.stroke()
    a_360 = window(t, Sk("c0_360", 0.2), Sk("c0_q72", 0.0), 0.4, 0.2)
    text(ctx, "360度", cx, cy, 84, INK, alpha=a_360)
    # 7.2度のくさび
    w72 = math.radians(7.2)
    a_w = fade(t, Sk("c0_q72", 0.15), 0.4)
    if a_w > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * a_w))
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + w72)
        ctx.close_path()
        ctx.fill()
        label(ctx, "7.2度", cx + 150, cy - r - 52, 56, RED, a_w)
        arrow2(ctx, (cx + 150, cy - r - 24), (cx + 18, cy - r + 8), RED, 4, a_w * 0.85, head=16)
    a_q = window(t, Sk("c0_q72", 0.35), Sk("c0_50", 0.0), 0.4, 0.2)
    text(ctx, "円の何分の1？", cx, cy + 70, 56, INK, alpha=a_q)
    # 50に分ける
    p50 = clamp01((t - Sk("c0_50", 0.35)) / 1.6)
    if p50 > 0:
        n = int(round(50 * ease_out(p50)))
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.9))
        ctx.set_line_width(2.5)
        for k in range(n):
            a_ = -math.pi / 2 + k * w72
            ctx.move_to(cx, cy)
            ctx.line_to(cx + r * math.cos(a_), cy + r * math.sin(a_))
            ctx.stroke()
        ctx.set_source_rgba(*hexrgb(RED, 0.9))
        ctx.move_to(cx, cy)
        ctx.arc(cx, cy, r, -math.pi / 2, -math.pi / 2 + w72)
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 1))
        ctx.set_line_width(8)
        ctx.arc(cx, cy, r, 0, 2 * math.pi)
        ctx.stroke()
    a_f = fade(t, Sk("c0_50", 0.55), 0.4)
    label(ctx, "360 ÷ 7.2 ＝ 50", cx, cy + r + 85, 60, INK, a_f)
    label(ctx, "答えは 50分の1", cx, cy + r + 165, 60, RED, fade(t, Sk("c0_50", 0.8), 0.4))


def L_earthB(ctx, t):
    """地球の断面図: 平行な光 → 棒を中心まで → 南は光と重なる → 北は光から傾く → 中心角も同じ → 弧は円の1/50"""
    V = VB
    earth_body(ctx, V)
    baseS, tipS = cpt(V, PHI_S, V[2]), cpt(V, PHI_S, V[2] + STICK_B)
    baseN, tipN = cpt(V, PHI_N, V[2]), cpt(V, PHI_N, V[2] + STICK_B)
    ps = PHI_S                                              # 光は南の棒と平行（太陽は南の棒の真上）
    a_par = fade(t, Sk("c0_par", 0.4), 0.6)
    col_s = BLUE if t > Sk("c0_sov", 0.2) else BROWN
    col_n = ORANGE if t > Sk("c0_nov", 0.2) else BROWN
    ray_col_s = BLUE if t > Sk("c0_sov", 0.2) else "#e3a21a"
    offs = [-0.62 * V[2], -0.31 * V[2], 0.0, 0.31 * V[2], ray_offset_through(V, ps, tipN)]
    if a_par > 0.003:
        sx, sy = V[0] + ((V[1] - 110.0) / math.cos(ps)) * math.sin(ps), 110.0
        sun_disc(ctx, sx, sy, 38, a_par)
        parallel_rays(ctx, V, ps, offs, a_par, y_top=150.0, hl={0.0: ray_col_s, offs[-1]: ORANGE if t > Sk("c0_nov", 0.2) else "#e3a21a"})
    # 町と町のあいだ（弧）
    arc_on(ctx, V, PHI_S, PHI_N, V[2] - 3, ORANGE if t > Sk("c0_arc", 0.2) else "#c9a46a", 9.0, 1.0)
    # 棒を中心まで
    pe = clamp01((t - Sk("c0_ext", 0.15)) / 1.3)
    if pe > 0:
        for b_, c_ in ((baseS, col_s), (baseN, col_n)):
            end = (b_[0] + (V[0] - b_[0]) * ease_out(pe), b_[1] + (V[1] - b_[1]) * ease_out(pe))
            line2(ctx, b_, end, c_, 6, 0.9, dash=[14, 10])
        ctx.set_source_rgba(*hexrgb(INK, ease_out(pe)))
        ctx.arc(V[0], V[1], 7, 0, 2 * math.pi)
        ctx.fill()
    stick_and_shadow(ctx, V, PHI_S, ps, STICK_B, col_s)
    stick_and_shadow(ctx, V, PHI_N, ps, STICK_B, col_n)
    # 北の棒と光のあいだの角（同じ色で中心の角にも）
    ang_col = RED
    a_nov = fade(t, Sk("c0_nov", 0.5), 0.4)
    if a_nov > 0.003:
        un = U(PHI_N)
        line2(ctx, tipN, (tipN[0] + 125 * un[0], tipN[1] + 125 * un[1]), col_n, 5, 0.9 * a_nov, dash=[10, 8])
        ctx.set_source_rgba(*hexrgb(ang_col, a_nov))
        ctx.set_line_width(7)
        ctx.arc_negative(tipN[0], tipN[1], 100, PHI_N - math.pi / 2, PHI_S - math.pi / 2)
        ctx.stroke()
        label(ctx, "7.2度", tipN[0] + 130, tipN[1] - 100, 52, ang_col, a_nov)
    a_cen = fade(t, Sk("c0_cen", 0.45), 0.4)
    if a_cen > 0.003:
        ctx.set_source_rgba(*hexrgb(ang_col, 0.28 * a_cen))
        ctx.move_to(*V[:2])
        ctx.arc(V[0], V[1], 110, PHI_S - math.pi / 2, PHI_N - math.pi / 2)
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(ang_col, a_cen))
        ctx.set_line_width(7)
        ctx.arc(V[0], V[1], 110, PHI_S - math.pi / 2, PHI_N - math.pi / 2)
        ctx.stroke()
        label(ctx, "7.2度", V[0], V[1] - 190, 52, ang_col, a_cen)
    # 札
    label(ctx, "南の町", baseS[0] - 122, 300, 46, INK, fade(t, Sk("c0_why", 0.6), 0.4))
    label(ctx, "北の町", baseN[0] + 122, 300, 46, INK, fade(t, Sk("c0_why", 0.6), 0.4))
    a_arc = fade(t, Sk("c0_arc", 0.5), 0.4)
    if a_arc > 0.003:
        label(ctx, "円の1/50", V[0], V[1] + 150, 60, ORANGE, a_arc)
        label(ctx, "地球の中心", V[0], V[1] + 235, 46, INK, a_arc * fade(t, Sk("c0_arc", 0.5), 0.4))
    label(ctx, "※ 角度は大きく描いてあります", 492, 912, 40, PENCIL_T, fade(t, Sk("c0_why", 0.5), 0.4))


RING = (492.0, 540.0, 285.0)


def ring_k(t):
    return int(round(50 * ease_in_out(clamp01((t - Sk("c0_x50", 0.12)) / (0.62 * Dk("c0_x50"))))))


def L_ring(ctx, t):
    """円を50個に分けた弧。1つ目が2つの町のあいだ（約800km）。50個ぶん並べると地球一周"""
    cx, cy, r = RING
    w72 = 2 * math.pi / 50
    a0 = fade(t, Sk("c0_800", 0.0), 0.4)
    k = ring_k(t) if t >= Sk("c0_x50", 0.1) else 1
    for i in range(50):
        if i >= max(k, 1):
            ctx.set_source_rgba(*hexrgb("#d6d0bd", 0.9 * a0))
        else:
            ctx.set_source_rgba(*hexrgb(RED if i == 0 else (BLUE if i % 2 else ORANGE), a0))
        ctx.set_line_width(34)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)
        s0 = -math.pi / 2 + i * w72 + 0.012
        ctx.arc(cx, cy, r, s0, s0 + w72 - 0.024)
        ctx.stroke()
    a_l = fade(t, Sk("c0_800", 0.55), 0.4)
    if a_l > 0.003:
        top = (cx + r * math.sin(w72 / 2), cy - r * math.cos(w72 / 2))
        arrow2(ctx, (cx + 150, 190), (top[0] + 6, top[1] - 24), RED, 5, a_l, head=18)
        label(ctx, "約800km", cx + 190, 160, 60, RED, a_l)
    text(ctx, "地球一周", cx, cy - 55, 56, INK, alpha=fade(t, Sk("c0_800", 0.3), 0.4))
    a_m = fade(t, Sk("c0_x50", 0.05), 0.4)
    text(ctx, "約800km × 50", cx, cy + 20, 56, BLUE, alpha=a_m)
    a_ans = fade(t, Sk("c0_x50", 0.62), 0.5)
    text(ctx, "約4万km", cx, cy + 110, 84, RED, alpha=a_ans)


# ============================================================
# 1万回の答えのヒストグラム（左ページ）。順番に積み上がる。当たりの帯（±10%→±5%）・本当の値・中央値
# ============================================================
BLUE_L = "#b9cdee"
LOSS_L = lk.LOSS_C
TICKS_WIDE = [(30000, "3万"), (40000, "4万"), (50000, "5万"), (60000, "6万")]
TICKS_NARROW = [(36000, "3.6万"), (40000, "4万"), (44000, "4.4万")]


class Hist:
    def __init__(self, samples, lo, hi, binw, x0=135.0, x1=870.0, base_y=730.0, hmax=380.0, ticks=None, special=False, peak=None):
        self.s = np.asarray(samples, float)
        self.lo, self.hi, self.binw = float(lo), float(hi), float(binw)
        self.edges = np.arange(lo, hi + 1e-6, binw)
        self.nb = len(self.edges) - 1
        self.x0, self.x1, self.by, self.hmax = x0, x1, base_y, hmax
        self.ticks = ticks or []
        self.special = special                          # 左端に「測れない ×」（答えが0以下）、右端に「範囲の外」
        full = np.histogram(self.s, bins=self.edges)[0]
        self.peak = float(peak or max(full.max(), 1))
        if special:
            self.peak = float(max(self.peak, (self.s <= 0).sum()))
        self.n_full = len(self.s)

    def x(self, v):
        return self.x0 + (v - self.lo) / (self.hi - self.lo) * (self.x1 - self.x0)

    def counts(self, k):
        return np.histogram(self.s[:k], bins=self.edges)[0]

    def frame(self, ctx, a=1.0, band=None, true_line=True, tick_size=44):
        """枠（軸・目もり・当たりの帯・本当の値の点線）"""
        if a <= 0.003:
            return
        if band:
            lo_, hi_ = band
            ctx.set_source_rgba(*hexrgb(BLUE, 0.13 * a))
            ctx.rectangle(self.x(lo_), self.by - self.hmax - 12, self.x(hi_) - self.x(lo_), self.hmax + 12)
            ctx.fill()
            for v in (lo_, hi_):
                line2(ctx, (self.x(v), self.by - self.hmax - 12), (self.x(v), self.by), BLUE, 3, 0.8 * a, dash=[9, 8])
        line2(ctx, (self.x0 - 10, self.by), (self.x1 + 10, self.by), INK, 5, a)
        for v, s_ in self.ticks:
            line2(ctx, (self.x(v), self.by), (self.x(v), self.by + 14), INK, 4, a)
            text(ctx, s_, self.x(v), self.by + 52, tick_size, INK, alpha=a)
        if true_line:
            line2(ctx, (self.x(C_T), self.by - self.hmax - 12), (self.x(C_T), self.by), RED, 5, 0.95 * a, dash=[14, 9])

    def bars(self, ctx, k, band=None, a=1.0, ghost=None, col_in=BLUE, col_out=LOSS_L):
        if k <= 0 and ghost is None:
            return
        bw = (self.x1 - self.x0) / self.nb
        if ghost is not None:
            gc = np.histogram(ghost, bins=self.edges)[0] / self.peak
            ctx.set_source_rgba(*hexrgb("#6b7285", 0.8 * a))
            ctx.set_line_width(3)
            ctx.set_dash([8, 6])
            for i in range(self.nb):
                hh = min(1.0, gc[i]) * self.hmax
                ctx.move_to(self.x0 + i * bw, self.by - hh)
                ctx.line_to(self.x0 + (i + 1) * bw, self.by - hh)
                if i + 1 < self.nb:
                    h2 = min(1.0, gc[i + 1]) * self.hmax
                    ctx.line_to(self.x0 + (i + 1) * bw, self.by - h2)
            ctx.stroke()
            ctx.set_dash([])
        if k <= 0:
            return
        c = self.counts(k) / self.peak
        for i in range(self.nb):
            hh = min(1.0, c[i]) * self.hmax
            if hh < 0.5:
                continue
            centre = self.edges[i] + self.binw / 2
            inside = band is not None and band[0] <= centre <= band[1]
            ctx.set_source_rgba(*hexrgb(col_in if inside else col_out, 0.95 * a))
            ctx.rectangle(self.x0 + i * bw + 0.5, self.by - hh, bw - 1.0, hh)
            ctx.fill()
        if self.special:
            neg = float((self.s[:k] <= 0).sum()) / self.peak
            over = float((self.s[:k] > self.hi).sum()) / self.peak
            for x_, v_, col in ((self.x0 - 100, neg, "#9aa3b5"), (self.x1 + 30, over, LOSS_L)):
                hh = min(1.0, v_) * self.hmax
                if hh > 0.5:
                    ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
                    ctx.rectangle(x_, self.by - hh, 52, hh)
                    ctx.fill()

    def n_in(self, k, band):
        return int(((self.s[:k] >= band[0]) & (self.s[:k] <= band[1])).sum())


BAND10 = (C_T * 0.90, C_T * 1.10)
BAND5 = (C_T * 0.95, C_T * 1.05)
H_WIDE = {k: Hist(SMP[k], 25000, 65000, 1000, ticks=TICKS_WIDE, peak=max(np.histogram(SMP[x], bins=np.arange(25000, 65001, 1000))[0].max() for x in ("S1", "S2"))) for k in ("S1", "S2")}
H_NARROW = {k: Hist(SMP[k], 34000, 46000, 250, ticks=TICKS_NARROW, peak=max(np.histogram(SMP[x], bins=np.arange(34000, 46001, 250))[0].max() for x in ("S3", "S4", "S5"))) for k in ("S3", "S4", "S5")}


def ff(t, gid):
    """早回しの区間 gid で 0→1（ゆっくり始まって速くなって止まる）"""
    return ease_in_out(clamp01((t - S(gid)) / max(dur(gid), 1e-6)))


def L_hist(ctx, t, H, gid, band_fn, t_frame, caption="1万回やり直した答え", k_full=None, ghost=None, show_true_label=True, true_t=None, extra=None, a_frame_fn=None):
    """gid の早回しで積み上がるヒストグラム。早回しの前は枠だけ、後は全部"""
    af = fade(t, t_frame, 0.5)
    band = band_fn(t)
    f = ff(t, gid) if gid else 1.0
    k = int(round(f * H.n_full)) if k_full is None else k_full
    H.frame(ctx, af, band)
    H.bars(ctx, k, band, af, ghost=ghost)
    text(ctx, caption, 110, 120, 48, INK, align="left", alpha=af)
    if show_true_label:
        tt = true_t if true_t is not None else t_frame
        label(ctx, "本当の値 約4万km", H.x(C_T), 205, 44, RED, fade(t, tt, 0.4) * af)
    if gid and 0.0 < f < 1.0:
        text(ctx, f"{k:,}回", 870, 120, 52, INK, align="right", alpha=af)
    if extra:
        extra(ctx, t, H, band, af)


# ============================================================
# ch1 の図: 棒1本の測り方（棒1m・目で読む・影の先のぼやけ・距離のぶれ）
# ============================================================
def blur_tip(ctx, x, y, w=70, h=16, a=1.0, sharp=False, col="#2d3548"):
    """影の先。ぼやけた（左は濃く右へ薄れる）か、くっきりか"""
    if sharp:
        ctx.set_source_rgba(*hexrgb(col, 0.85 * a))
        ctx.rectangle(x - 150, y - h / 2, 150, h)
        ctx.fill()
        return
    g = cairo.LinearGradient(x - w, 0, x + w, 0)
    g.add_color_stop_rgba(0, *hexrgb(col, 0.85 * a)[:3], 0.85 * a)
    g.add_color_stop_rgba(0.45, *hexrgb(col, 0.85 * a)[:3], 0.85 * a)
    g.add_color_stop_rgba(1, *hexrgb(col, 0.0)[:3], 0.0)
    ctx.set_source(g)
    ctx.rectangle(x - 150, y - h / 2, 150 + w, h)
    ctx.fill()


def L_stickfig(ctx, t):
    gy, bx, h = 540.0, 250.0, 250.0
    sunp = (125.0, 135.0)
    tip = (bx, gy - h)
    dx, dy = tip[0] - sunp[0], tip[1] - sunp[1]
    n_ = math.hypot(dx, dy)
    ux, uy = dx / n_, dy / n_
    s_ = (gy - tip[1]) / uy
    sh = (tip[0] + s_ * ux, gy)                                           # 影の先
    line2(ctx, (80, gy), (880, gy), EARTH_L, 7)
    a_s = fade(t, Sk("c1_stick", 0.0) - 0.4, 0.4)
    line2(ctx, (bx, gy), sh, "#2d3548", 13, 0.85 * a_s, cap=cairo.LINE_CAP_BUTT)
    line2(ctx, (bx, gy), tip, BROWN, 15, a_s)
    line2(ctx, sunp, sh, "#e3a21a", 5, 0.85 * a_s)
    arrowhead(ctx, sh, (ux, uy), "#e3a21a", 20, 0.85 * a_s, 5)
    sun_disc(ctx, sunp[0], sunp[1], 40, a_s)
    label(ctx, "棒 1m", bx - 98, gy - h * 0.5, 48, INK, a_s)
    label(ctx, "影", (bx + sh[0]) / 2, gy + 58, 48, INK, a_s)
    a_r = fade(t, Sk("c1_read", 0.1), 0.4)
    if a_r > 0.003:
        arrow2(ctx, (sh[0] - 34, gy + 110), (sh[0] + 34, gy + 110), RED, 5, a_r, both=True, head=16)
        line2(ctx, (sh[0] - 34, gy + 92), (sh[0] - 34, gy + 128), RED, 4, a_r)
        line2(ctx, (sh[0] + 34, gy + 92), (sh[0] + 34, gy + 128), RED, 4, a_r)
        label(ctx, "読み取り ±1.5cm", sh[0] + 240, gy + 110, 46, RED, a_r)
    a_b = fade(t, Sk("c1_blur", 0.1), 0.4)
    if a_b > 0.003:
        blur_tip(ctx, sh[0] + 46, gy, 72, 16, a_b)
        pen_circle(ctx, sh[0] + 6, gy, 74, 36, ORANGE, seed=4, width=6, progress=clamp01((t - Sk("c1_blur", 0.1)) / 0.7), alpha=a_b)
        label(ctx, "影の先は ぼやける", sh[0] + 250, gy - 70, 46, ORANGE, a_b)
    # 2つの町の距離のぶれ
    a_d = fade(t, Sk("c1_dist", 0.05), 0.4)
    if a_d > 0.003:
        y0 = 800.0
        for x_ in (190.0, 790.0):
            ctx.set_source_rgba(*hexrgb(INK, a_d))
            ctx.arc(x_, y0, 15, 0, 2 * math.pi)
            ctx.fill()
        arrow2(ctx, (214, y0), (738, y0), BLUE, 6, a_d, head=20)
        g = cairo.LinearGradient(700, 0, 830, 0)
        g.add_color_stop_rgba(0, *hexrgb(BLUE, 0.0)[:3], 0.0)
        g.add_color_stop_rgba(0.5, *hexrgb(BLUE, 0.5)[:3], 0.5 * a_d)
        g.add_color_stop_rgba(1, *hexrgb(BLUE, 0.0)[:3], 0.0)
        ctx.set_source(g)
        ctx.rectangle(700, y0 - 14, 130, 28)
        ctx.fill()
        label(ctx, "南の町", 190, y0 + 65, 44, INK, a_d)
        label(ctx, "北の町", 790, y0 + 65, 44, INK, a_d)
        label(ctx, "距離 ±10%", 490, y0 - 62, 48, BLUE, a_d)


def L_stick10(ctx, t):
    """棒が10倍なら影も10倍。同じ1.5cmのぶれは、影に対して10分の1"""
    gy = 790.0
    sc = 44.0                                             # 1m = 44px
    th = math.radians(28)
    xs = (210.0, 520.0)
    line2(ctx, (80, gy), (880, gy), EARTH_L, 7)
    a1 = fade(t, Sk("c1_add", 0.1), 0.4)
    for x_, hm, nm in ((xs[0], 1, "棒 1m"), (xs[1], 10, "棒 10m")):
        h = hm * sc
        grow = ease_out(clamp01((t - Sk("c1_x10", 0.0)) / 1.2)) if hm == 10 else 1.0
        h_ = h if hm == 1 else max(sc, h * grow)
        sh = h_ * math.tan(th)
        if hm == 10 and grow < 1:
            pass
        line2(ctx, (x_, gy), (x_ + sh, gy), "#2d3548", 12, 0.85 * a1, cap=cairo.LINE_CAP_BUTT)
        line2(ctx, (x_, gy), (x_, gy - h_), BROWN, 15, a1)
        label(ctx, nm, x_ - 5 if hm == 1 else x_ - 95, gy - h_ - 52 if hm == 1 else gy - h_ / 2, 48, INK, a1)
        # 同じ大きさの読み取りのぶれ（影の先）
        a_b = fade(t, Sk("c1_x10", 0.2), 0.4)
        tx = x_ + sh
        line2(ctx, (tx - 9, gy + 40), (tx + 9, gy + 40), RED, 6, a_b)
        line2(ctx, (tx - 9, gy + 28), (tx - 9, gy + 52), RED, 4, a_b)
        line2(ctx, (tx + 9, gy + 28), (tx + 9, gy + 52), RED, 4, a_b)
    a_s = fade(t, Sk("c1_x10", 0.55), 0.4)
    label(ctx, "同じ1.5cm", 640, gy + 92, 46, RED, a_s)
    a_t = fade(t, Sk("c1_tenth", 0.75), 0.4)
    label(ctx, "ぶれは 影の 1/10", 560, 250, 58, RED, a_t)
    label(ctx, "影が10倍長い", 560, 180, 50, INK, fade(t, Sk("c1_x10", 0.4), 0.4))


# ============================================================
# ch2 の図: 距離のぶれ 10% → 2%、ぶれの内訳
# ============================================================
def L_dist2(ctx, t):
    y0 = 450.0
    a = fade(t, Sk("c2_dist", 0.0) - 0.4, 0.4)
    for x_ in (170.0, 760.0):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(x_, y0, 18, 0, 2 * math.pi)
        ctx.fill()
    arrow2(ctx, (196, y0), (700, y0), BLUE, 8, a, head=24)
    sh = clamp01((t - Sk("c2_2pct", 0.55)) / 0.9)
    fz = lerp(0.10, 0.02, ease_in_out(sh)) * 560
    g = cairo.LinearGradient(700 - fz, 0, 700 + fz, 0)
    g.add_color_stop_rgba(0, *hexrgb(BLUE, 0.0)[:3], 0.0)
    g.add_color_stop_rgba(0.5, *hexrgb(BLUE, 0.55)[:3], 0.55 * a)
    g.add_color_stop_rgba(1, *hexrgb(BLUE, 0.0)[:3], 0.0)
    ctx.set_source(g)
    ctx.rectangle(700 - fz, y0 - 22, 2 * fz, 44)
    ctx.fill()
    label(ctx, "南の町", 170, y0 + 75, 48, INK, a)
    label(ctx, "北の町", 760, y0 + 75, 48, INK, a)
    label(ctx, "距離のぶれ", 460, y0 - 130, 56, BLUE, a)
    a1 = out_fade(t, Sk("c2_2pct", 0.55), 0.2)
    text(ctx, "10%", 460, y0 - 60, 64, RED, alpha=a * a1)
    a2 = fade(t, Sk("c2_2pct", 0.55) + 0.25, 0.4)
    text(ctx, "2%", 460, y0 - 60, 64, RED, alpha=a * a2)
    label(ctx, "ぶれが小さい", 460, y0 + 190, 52, BLUE, a * fade(t, Sk("c2_2pct", 0.8), 0.4))


BD = RES["breakdown"]["before"]
BREAK_ROWS = [lk.Row("距離", BD["distance"], t_label=0.0, t_value=0.0, color=RED, line=ID["c2_break"], text=""),
              lk.Row("影の先の癖", BD["habit"], t_label=0.0, t_value=0.0, color=ORANGE, line=ID["c2_break"], text=""),
              lk.Row("影の読み取り", BD["reading"], t_label=0.0, t_value=0.0, color=GREEN, line=ID["c2_break"], text="")]
T_BREAK0 = Sk("c2_break", 0.0) - 1.4
for _i, _r in enumerate(BREAK_ROWS):
    _r.t_label = T_BREAK0 + 0.1 * _i
    _r.t_value = Sk("c2_break", 0.28) + 0.35 * _i
BREAK = lk.LadderPanel("ぶれの大きさ（1つずつ）", BREAK_ROWS, box=(95, 240, 905, 660), t_frame=T_BREAK0, vmax=0.11, fmt=lambda v: "", plus=False, arrows=False,
                       label_size=44, val_size=44, title_line=ID["c2_break"], fade=0.4)


def L_break(ctx, t):
    BREAK.draw(ctx, t)
    a = fade(t, Sk("c2_break", 0.55), 0.4)
    label(ctx, "いちばん大きいのは 距離", 500, 760, 52, RED, a)


# ============================================================
# ch3 の図: 10日測って平均／影の先のぼやけ→癖／くっきり
# ============================================================
_RNG_D = np.random.default_rng(7)
DAY_JIT = _RNG_D.normal(0, 7.0, 10)


def L_days(ctx, t):
    gy = 560.0
    th = math.radians(24)
    h = 190.0
    shl = h * math.tan(th)
    line2(ctx, (80, gy), (885, gy), EARTH_L, 7)
    t0 = Sk("c3_cal", 0.0)
    for i in range(10):
        a = fade(t, t0 + 0.28 * i - 0.4, 0.35)
        x_ = 112.0 + 77.0 * i
        hh = 150.0
        sl = hh * math.tan(th)
        line2(ctx, (x_, gy), (x_ + sl, gy), "#2d3548", 8, 0.8 * a, cap=cairo.LINE_CAP_BUTT)
        line2(ctx, (x_, gy), (x_, gy - hh), BROWN, 9, a)
        ex = x_ + sl + DAY_JIT[i]
        ctx.set_source_rgba(*hexrgb(RED, a))
        ctx.arc(ex, gy, 6, 0, 2 * math.pi)
        ctx.fill()
        text(ctx, str(i + 1), x_ + 22, gy + 52, 40, INK, alpha=a)
    a_c = fade(t, t0 - 0.4, 0.4)
    label(ctx, "毎日 正午に測る", 492, 200, 54, INK, a_c)
    a_avg = fade(t, Sk("c3_avg", 0.6), 0.5)
    if a_avg > 0.003:
        ctx.set_source_rgba(*hexrgb(GREEN, a_avg))
        ctx.set_line_width(7)
        ctx.move_to(112, gy + 108)
        ctx.line_to(112, gy + 126)
        ctx.line_to(112 + 77 * 9 + 70, gy + 126)
        ctx.line_to(112 + 77 * 9 + 70, gy + 108)
        ctx.stroke()
        arrow2(ctx, (492, gy + 126), (492, gy + 200), GREEN, 6, a_avg, head=18)
        label(ctx, "10日分を 平均", 492, gy + 245, 54, GREEN, a_avg)
        label(ctx, "読み取りのぶれは 小さくなる", 492, gy + 320, 48, GREEN, a_avg * fade(t, Sk("c3_avg", 0.85), 0.4))


def L_tip(ctx, t):
    """影の先のぼやけ → どこで読むかの癖（毎日同じ位置）。くっきり読める道具ならその癖が小さい"""
    gy1, gy2 = 360.0, 700.0
    xtip = 650.0
    for gy, sharp, nm, tcol in ((gy1, False, "ぼやけた影の先", ORANGE), (gy2, True, "くっきりした影の先", GREEN)):
        a = 1.0
        if sharp:
            a = fade(t, Sk("c3_tool", 0.0) - 0.4, 0.4)
        else:
            a = fade(t, Sk("c3_habit", 0.0) - 0.5, 0.4)
        if a <= 0.003:
            continue
        line2(ctx, (80, gy + 30), (885, gy + 30), EARTH_L, 6, a)
        blur_tip(ctx, xtip, gy, 90 if not sharp else 0, 26, a, sharp=sharp)
        if sharp:
            line2(ctx, (xtip - 150, gy), (xtip + 12, gy), "#2d3548", 26, 0.85 * a, cap=cairo.LINE_CAP_BUTT)
        label(ctx, nm, 492, gy - 105, 50, tcol, a)
        # 読む位置の印（毎日同じ）
        hx = xtip + (30 if not sharp else 0)
        ah = a * fade(t, (Sk("c3_habit", 0.45) if not sharp else Sk("c3_tool", 0.3)), 0.4)
        if ah > 0.003:
            arrow2(ctx, (hx, gy - 62), (hx, gy - 22), RED, 6, ah, head=16)
            label(ctx, "ここで読む", hx + 4, gy + 85, 46, RED, ah)
    a_same = fade(t, Sk("c3_always", 0.1), 0.4)
    label(ctx, "毎日 同じ位置で読む", 330, gy1 + 155, 48, RED, a_same)


# ============================================================
# ch4 の図: エラトステネスの考え方 vs 正しい計算／緯度／太陽の向き／町の並び
# ============================================================
def L_ruler(ctx, t):
    lo, hi = 39000.0, 41200.0
    xr = lambda v: 130.0 + (v - lo) / (hi - lo) * 740.0
    y = 470.0
    a = fade(t, S("ch4") + 0.3, 0.5)
    line2(ctx, (110, y), (890, y), INK, 6, a)
    text(ctx, "測りまちがい ゼロ", 492, 175, 60, INK, alpha=a * fade(t, Sk("c4_zero", 0.1), 0.4))
    # 本当の値
    line2(ctx, (xr(C_T), y - 130), (xr(C_T), y + 16), RED, 6, a, dash=[14, 9])
    label(ctx, "本当の値", xr(C_T), 545, 46, RED, a)
    # エラトステネスの考え方
    a_e = fade(t, Sk("c4_632", 0.5), 0.5)
    xe = xr(RES["consts"]["no_err"])
    ctx.set_source_rgba(*hexrgb(ORANGE, a_e))
    ctx.arc(xe, y, 17, 0, 2 * math.pi)
    ctx.fill()
    label(ctx, "エラトステネスの考え方", 560, 255, 46, ORANGE, a_e)
    arrow2(ctx, (xe, 280), (xe, y - 24), ORANGE, 4, a_e * 0.9, head=14)
    text(ctx, f"{ihalf(RES['consts']['no_err']):,}km", xe, 620, 52, ORANGE, alpha=a_e)
    # +1.6%
    a_p = fade(t, Sk("c4_16", 0.3), 0.4)
    if a_p > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, a_p))
        ctx.set_line_width(6)
        ctx.move_to(xr(C_T), y - 60)
        ctx.line_to(xr(C_T), y - 82)
        ctx.line_to(xe, y - 82)
        ctx.line_to(xe, y - 60)
        ctx.stroke()
        label(ctx, "＋1.6%", (xr(C_T) + xe) / 2, y - 140, 64, RED, a_p)
    a_c = fade(t, Sk("c4_cor", 0.55), 0.4)
    label(ctx, f"正しい計算 {ihalf(RES['consts']['correct']):,}km", xr(C_T) + 6, 700, 52, BLUE, a_c)
    if a_c > 0.003:
        arrow2(ctx, (xr(C_T), 676), (xr(C_T), y + 56), BLUE, 4, a_c * 0.9, head=14)


def L_lat(ctx, t):
    """緯度とは、赤道から北へ進んだ角度。2つの町の緯度の差が本当の角度"""
    C0 = (430.0, 600.0)
    r = 280.0
    V = (C0[0], C0[1], r)
    phS, phN = math.radians(90 - LAT_S), math.radians(90 - LAT_A)
    a = fade(t, Sk("c4_lat", 0.0) - 0.4, 0.4)
    earth_body(ctx, V, a)
    line2(ctx, C0, (C0[0] + r + 70, C0[1]), INK, 6, a)
    label(ctx, "赤道", C0[0] + r + 15, C0[1] + 60, 46, INK, a)
    pS, pN = cpt(V, phS, r), cpt(V, phN, r)
    # 緯度（赤道から北へ）
    a_l = fade(t, Sk("c4_lat", 0.25), 0.5)
    arc_on(ctx, V, math.pi / 2, phN, 130, ORANGE, 8, a_l)
    line2(ctx, C0, pN, ORANGE, 5, a_l, dash=[12, 9])
    label(ctx, "緯度", C0[0] + 195, C0[1] - 58, 52, ORANGE, a_l)
    a_d = fade(t, Sk("c4_diff", 0.1), 0.4)
    line2(ctx, C0, pS, BLUE, 5, a_d, dash=[12, 9])
    if a_d > 0.003:
        ctx.set_source_rgba(*hexrgb(RED, 0.35 * a_d))
        ctx.move_to(*C0)
        ctx.arc_negative(C0[0], C0[1], r - 4, phS - math.pi / 2, phN - math.pi / 2)
        ctx.close_path()
        ctx.fill()
        arc_on(ctx, V, phS, phN, r + 8, RED, 10, a_d)
        arrow2(ctx, (610, 335), (pN[0] + 6, pN[1] - 8), RED, 4, a_d, head=16)
        label(ctx, "緯度の差", 590, 305, 54, RED, a_d)
    for p_, nm, dy_ in ((pN, "北の町", -62), (pS, "南の町", 62)):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(p_[0], p_[1], 9, 0, 2 * math.pi)
        ctx.fill()
        label(ctx, nm, p_[0] + 100, p_[1] + dy_, 46, INK, a)
    a_c = fade(t, Sk("c4_cor", 0.2), 0.4)
    label(ctx, "南北の道のり ÷ 緯度の差 × 360", 492, 905, 46, BLUE, a_c)


def L_sunoff(ctx, t):
    """当時のシエネの太陽は真上から0.4度ずれていた → 0度として計算 → 北の町の角度が大きく読まれる → 一周は小さく出る"""
    gy, bx, h = 690.0, 230.0, 270.0
    th = math.radians(12)                                  # 大きく描く（本当は0.4度）
    a = fade(t, Sk("c4_sun", 0.0) - 0.4, 0.4)
    line2(ctx, (80, gy), (470, gy), EARTH_L, 7, a)
    tip = (bx, gy - h)
    sunp = (tip[0] - 250 * math.sin(th), tip[1] - 250 * math.cos(th))
    sh = tip[0] + h * math.tan(th)
    line2(ctx, (bx, gy), (sh, gy), "#2d3548", 12, 0.85 * a, cap=cairo.LINE_CAP_BUTT)
    line2(ctx, sunp, (sh, gy), "#e3a21a", 5, 0.85 * a)
    arrowhead(ctx, (sh, gy), (math.sin(th), math.cos(th)), "#e3a21a", 20, 0.85 * a, 5)
    sun_disc(ctx, sunp[0], sunp[1], 36, a)
    line2(ctx, (bx, gy), tip, BROWN, 14, a)
    line2(ctx, tip, (bx, tip[1] - 200), "#9aa3b5", 4, 0.9 * a, dash=[10, 9])
    ctx.set_source_rgba(*hexrgb(RED, a))
    ctx.set_line_width(6)
    ctx.arc_negative(tip[0], tip[1], 130, -math.pi / 2, -math.pi / 2 - th)
    ctx.stroke()
    label(ctx, "0.4度", tip[0] - 95, tip[1] - 110, 54, RED, a * fade(t, Sk("c4_sun", 0.5), 0.4))
    label(ctx, "真上", bx + 55, tip[1] - 175, 44, PENCIL_T, a)
    label(ctx, "シエネの棒", 275, gy + 62, 46, INK, a)
    label(ctx, "※ 角度は大きく描いてあります", 350, 905, 40, PENCIL_T, a)
    # 順番に: 0度として計算 ↓ 北の町の角度が大きく読まれる ↓ 一周は小さく出る
    items = [("0度として\n計算した", Sk("c4_0deg", 0.2), "yellow", INK, 235), ("北の町の角度が\n大きく読まれる", Sk("c4_big", 0.3), "pink", RED, 445),
             ("地球一周は\n小さく出る", Sk("c4_small", 0.3), "mint", INK, 655)]
    for k, (s_, t0, col, fg, yy) in enumerate(items):
        aa = fade(t, t0, 0.4)
        mini_sticky(ctx, s_, 700, yy, 46, col, fg=fg, a=aa, tilt=-0.01 + 0.01 * k)
        if k < 2:
            arrow2(ctx, (700, yy + 82), (700, yy + 128), PENCIL_T, 5, fade(t, items[k + 1][1], 0.4), head=14)


def L_map4(ctx, t):
    """町の並び: 真南北ではなく東西にずれている。地図で結ぶと844km、北へ進んだ分は790km"""
    SP = (660.0, 800.0)
    k = 0.70                                              # 1km あたりの画素
    dy, dx = CONST["d_mer"] * k, CONST["d_ew"] * k
    AP = (SP[0] - dx, SP[1] - dy)
    a = fade(t, Sk("c4_pos", 0.0) - 0.3, 0.4)
    for p_, nm, off in ((AP, "北の町", (-120, 0)), (SP, "南の町", (0, 62))):
        ctx.set_source_rgba(*hexrgb(INK, a))
        ctx.arc(p_[0], p_[1], 14, 0, 2 * math.pi)
        ctx.fill()
        label(ctx, nm, p_[0] + off[0], p_[1] + off[1], 46, INK, a)
    arrow2(ctx, (120, 400), (120, 255), PENCIL_T, 6, a, head=18)
    label(ctx, "北", 120, 205, 50, PENCIL_T, a)
    a_ew = fade(t, Sk("c4_pos", 0.55), 0.4)
    line2(ctx, (SP[0], AP[1]), AP, ORANGE, 6, a_ew, dash=[12, 9])
    label(ctx, "東西にずれ", (SP[0] + AP[0]) / 2, AP[1] - 52, 46, ORANGE, a_ew)
    a_d = fade(t, Sk("c4_844", 0.3), 0.4)
    line2(ctx, SP, AP, RED, 9, a_d)
    label(ctx, "844km", (SP[0] + AP[0]) / 2 - 150, (SP[1] + AP[1]) / 2, 54, RED, a_d)
    a_n = fade(t, Sk("c4_790", 0.3), 0.4)
    line2(ctx, SP, (SP[0], AP[1]), BLUE, 9, a_n)
    label(ctx, "790km", SP[0] + 120, (SP[1] + AP[1]) / 2, 54, BLUE, a_n)
    a_l = fade(t, Sk("c4_844b", 0.3), 0.4)
    label(ctx, "斜めは 長すぎる → 一周は大きく出る", 480, 905, 44, RED, a_l)


# ============================================================
# ch5 の図: 町が近いと（100km）
# ============================================================
HN_C = Hist(np.array(NEAR_C[100]["samples"]), 0, 100000, 1000, x0=330, x1=860, base_y=520, hmax=220, ticks=[], special=True)
HN_F = Hist(np.array(NEAR_F[100]["samples"]), 0, 100000, 1000, x0=330, x1=860, base_y=790, hmax=170, ticks=[(20000, "2万"), (40000, "4万"), (60000, "6万"), (80000, "8万")])


DRAW_K = 32.0 / 7.2                                     # 角度を大きく描く倍率（7.2度 → 32度・0.9度 → 4度）
ANG_100 = RES["near_angle_100"]                         # 100kmの2本の棒の角度の差（度・data.json）
SUN_BLUR = 2 * CONST["sun_half"]                        # 影の先のぼやけの幅（度・約0.5度）


def L_near1(ctx, t):
    """第5章: 地球の弧に2組の棒（800km離れた組＝7.2度・100km離れた組＝0.9度）。下に角度の棒と、読み取りのずれの帯"""
    V = (492.0, 800.0, 520.0)
    a = fade(t, S("ch5") + 0.3, 0.5)
    ctx.save()
    ctx.rectangle(45, 36, 890, 524)
    ctx.clip()
    earth_body(ctx, V, a)
    pairs = [(math.radians(-40), math.radians(-40 + 7.2 * DRAW_K), "800km", "7.2度", a, fade(t, S("ch5") + 0.5, 0.4)),
             (math.radians(14), math.radians(14 + ANG_100 * DRAW_K), "100km", f"{ANG_100:.1f}度", fade(t, Sk("c5_100", 0.0) - 0.2, 0.5), fade(t, Sk("c5_100", 0.45), 0.4))]
    for p1, p2, dist, ang, ap, al in pairs:
        if ap <= 0.003:
            continue
        arc_on(ctx, V, p1, p2, V[2] - 3, ORANGE, 10.0, ap)
        for ph in (p1, p2):
            b_, t_ = cpt(V, ph, V[2]), cpt(V, ph, V[2] + 120)
            line2(ctx, b_, t_, BROWN, 13, ap)
        arc_on(ctx, V, p1, p2, V[2] + 150, RED, 7.0, ap)
        for ph in (p1, p2):
            line2(ctx, cpt(V, ph, V[2] + 122), cpt(V, ph, V[2] + 160), "#9aa3b5", 3, ap * 0.9, dash=[7, 6])
        mid = (p1 + p2) / 2
        lx, ly = cpt(V, mid, V[2] + 205)
        label(ctx, ang, lx, ly, 52, RED, ap * al)
        dx, dy = cpt(V, mid, V[2] - 68)
        label(ctx, dist, dx, dy, 46, INK, ap * fade(t, S("ch5") + 0.5 if dist == "800km" else Sk("c5_100", 0.0), 0.4))
    ctx.restore()
    label(ctx, "※ 角度は大きく描いてあります", 492, 590, 40, PENCIL_T, a)
    # 角度の棒（上から 800km・100km）と、読み取りのずれの帯
    s_, x0 = 64.0, 270.0
    t_row = Sk("c5_why", 0.0) - 1.0
    ar = fade(t, t_row, 0.4)
    rows = [("800km", 7.2, 680.0, BLUE, "7.2度"), ("100km", ANG_100, 775.0, ORANGE, f"{ANG_100:.1f}度")]
    for nm, deg, y, col, txt in rows:
        text(ctx, nm, 110, y, 44, INK, align="left", alpha=ar)
        ctx.set_source_rgba(1, 1, 1, 0.7 * ar)
        rrect(ctx, x0, y - 22, 8.0 * s_, 44, 6)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(col, 0.92 * ar))
        rrect(ctx, x0, y - 22, deg * s_, 44, 6)
        ctx.fill()
        xe = x0 + deg * s_
        ab = fade(t, Sk("c5_why", 0.35), 0.4)
        ctx.set_source_rgba(*hexrgb(RED, 0.33 * ab))
        ctx.rectangle(xe - SUN_BLUR * s_ / 2, y - 38, SUN_BLUR * s_, 76)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * ab))
        ctx.set_line_width(3)
        ctx.rectangle(xe - SUN_BLUR * s_ / 2, y - 38, SUN_BLUR * s_, 76)
        ctx.stroke()
        text(ctx, txt, xe + SUN_BLUR * s_ / 2 + 14, y, 44, col, align="left", alpha=ar)
    ab = fade(t, Sk("c5_why", 0.35), 0.4)
    xe2 = x0 + ANG_100 * s_
    arrow2(ctx, (xe2, 846), (xe2, 818), RED, 4, ab * 0.9, head=14)
    label(ctx, "読み取りのぶれ 約0.5度", 480, 878, 44, RED, ab)
    text(ctx, "差が ぶれに埋もれる", 700, 775, 40, RED, alpha=fade(t, Sk("c5_why", 0.6), 0.4))


def L_near(ctx, t):
    """第5章（丁寧な測り方のあと）: 同じ軸の2つの分布。雑な測り方は答えが負の回を「測れない ×」にする"""
    a = fade(t, S("ch5") + 0.3, 0.5)
    HN_C.frame(ctx, a, (BAND10[0], BAND10[1]), true_line=True)
    HN_F.frame(ctx, a, (BAND10[0], BAND10[1]), true_line=True)
    kf = int(HN_F.n_full * ease_out(clamp01((t - Sk("c5_desc", 0.1)) / 2.2)))
    HN_C.bars(ctx, HN_C.n_full, (BAND10[0], BAND10[1]), a)
    HN_F.bars(ctx, kf, (BAND10[0], BAND10[1]), a)
    label(ctx, "棒1m・目で読む", 600, 268, 46, INK, a)
    label(ctx, "＋影の先をくっきり", 600, 570, 46, INK, a)
    label(ctx, "測れない ×", 228, 290, 44, RED, a)


# ============================================================
# ch6 の図: スタディオン
# ============================================================
def L_stad(ctx, t):
    cx, cy = 492.0, 215.0
    a = fade(t, S("ch6") + 0.3, 0.5)
    # 競技場の走路（細長い輪）。まっすぐの1辺が1スタディオン
    ctx.set_source_rgba(*hexrgb("#e5dcc0", a))
    rrect(ctx, cx - 300, cy - 70, 600, 140, 70)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(EARTH_L, a))
    ctx.set_line_width(7)
    rrect(ctx, cx - 300, cy - 70, 600, 140, 70)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#f6f2e7", a))
    rrect(ctx, cx - 210, cy - 30, 420, 60, 30)
    ctx.fill()
    a_d = fade(t, Sk("c6_def", 0.0), 0.5)
    if a_d > 0.003:
        arrow2(ctx, (cx - 230, cy + 98), (cx + 230, cy + 98), RED, 6, a_d, both=True, head=18)
        label(ctx, "1スタディオン", cx, cy + 150, 52, RED, a_d)
    label(ctx, "古代ギリシャの 距離の単位", cx, 440, 44, PENCIL_T, a_d)
    # 25万スタディオン × ？m
    a_25 = fade(t, Sk("c6_25", 0.2), 0.4)
    mini_sticky(ctx, "25万スタディオン × ？m", 492, 535, 50, "yellow", a=a_25, tilt=-0.008)
    a_len = fade(t, Sk("c6_len", 0.3), 0.4)
    label(ctx, "決着していない", 492, 622, 58, RED, a_len)
    a1 = fade(t, Sk("c6_157", 0.3), 0.4)
    mini_sticky(ctx, f"× 157.5m ＝ 約{ihalf(CONST['stadion_157'] / 1000)}千km".replace("約39千km", "約3万9千km"), 492, 722, 50, "blue", fg=BLUE, a=a1, tilt=-0.008)
    a2 = fade(t, Sk("c6_185", 0.3), 0.4)
    mini_sticky(ctx, f"× 185m ＝ 約{ihalf(CONST['stadion_185'] / 1000)}千km".replace("約46千km", "約4万6千km"), 492, 826, 50, "pink", fg=RED, a=a2, tilt=0.008)


# ============================================================
# ch7: まとめ（左ページ）
# ============================================================
HS_A = Hist(SMP["S1"], 25000, 65000, 1000, x0=380, x1=880, base_y=330, hmax=150, ticks=[])
HS_B = Hist(SMP["S3"], 25000, 65000, 1000, x0=380, x1=880, base_y=560, hmax=150, ticks=[(30000, "3万"), (40000, "4万"), (50000, "5万"), (60000, "6万")])


def L_summ(ctx, t):
    a = fade(t, S("ch7") + 0.4, 0.5)
    for H_, nm, k_, t0, col in ((HS_A, "棒1m\n目で読む", "S1", Sk("c7_0", 0.05), 0), (HS_B, "＋距離を\nきちんと", "S3", Sk("c7_0", 0.4), 1)):
        ah = a * fade(t, t0 - 0.5, 0.5)
        H_.frame(ctx, ah, BAND10, true_line=True)
        H_.bars(ctx, int(H_.n_full * ease_out(clamp01((t - t0) / 1.2))), BAND10, ah)
        text(ctx, nm, 200, H_.by - 70, 46, INK, alpha=ah)
    a3 = fade(t, Sk("c7_3", 0.1), 0.5)
    text(ctx, "大事なのは\n影より、町の距離", 492, 715, 60, RED, alpha=a3)
    a4 = fade(t, Sk("c7_4", 0.05), 0.4)
    mini_sticky(ctx, "あなたなら、2つの町の距離を、\nどうやって正しく測りますか？", 492, 860, 44, "yellow", a=a4 * out_fade(t, T_ES - 0.1, 0.3), tilt=-0.01)


# ============================================================
# 層の時刻表（左ページ）
# ============================================================
LAYERS = []


def layer(name, t0, t1, fn, fi=0.4, fo=0.4):
    LAYERS.append((name, t0, t1, fn, fi, fo))


T_ES = Sk("c7_5", 0.0) - 0.3            # 終了画面の始まり（注意書きの文の頭の少し前から最後の約15秒）
T_BOX_OUT = Sk("c0_move", 0.0) - 0.25   # 冒頭の答えの箱（約4万km）が消える
SW = S("g2_2")                          # 基準を10%→5%に替える場面の切り替え（1秒）


def crit10(t):
    return BAND10


def crit_sw(t):
    """10%→5% の帯（切り替えの1秒の中で 0.1〜0.5秒かけて縮む）"""
    u = ease_in_out(clamp01((t - SW - 0.1) / 0.4))
    p = lerp(0.10, 0.05, u)
    return (C_T * (1 - p), C_T * (1 + p))


def crit5(t):
    return BAND5


def h1_frame(ctx, t):
    L_hist(ctx, t, H_WIDE["S1"], None, crit10, S("ch1") + 0.3, k_full=0, true_t=Sk("c1_true", 0.0) - 0.6)


def h1_grow(ctx, t):
    def extra(ctx, t, H, band, af):
        # 真ん中の線（4万600km）とばらつき
        am = fade(t, Sk("c1_med", 0.55), 0.4)
        xm = H.x(STEP["S1"]["med"])
        line2(ctx, (xm, 262), (xm, H.by), ORANGE, 5, am * af)
        label(ctx, f"中央値 {int(round(STEP['S1']['med'], -2) // 10000)}万{int(round(STEP['S1']['med'], -2) % 10000)}km", xm + 90, 268, 44, ORANGE, am * af)
        aw = fade(t, Sk("c1_wide", 0.2), 0.4)
        x10, x90 = H.x(STEP["S1"]["p10"]), H.x(STEP["S1"]["p90"])
        arrow2(ctx, (xm - 40, 560), (x10 - 6, 560), PENCIL_T, 6, aw * af, head=16)
        arrow2(ctx, (xm + 40, 560), (x90 + 6, 560), PENCIL_T, 6, aw * af, head=16)
        label(ctx, "ばらつく", xm + 235, 470, 50, PENCIL_T, aw * af)
    L_hist(ctx, t, H_WIDE["S1"], "g1_1", crit10, S("ch1") + 0.3, true_t=Sk("c1_true", 0.0) - 0.6, extra=extra)


GRID1 = lk.GridPanel(STEP["S1"]["n10"], caption="青＝10%以内の当たり　1マス＝1回", t_cap=Sk("c1_hit", 0.0) - 1.05, t0=Sk("c1_hit", 0.3), t1=Sk("c1_hit", 0.3) + 2.2,
                     t_count=Sk("c1_hit", 0.55), count_fmt="1万回のうち {wins:,}回")
GRID5 = lk.GridPanel(NEAR_F[100]["n10"], caption="青＝10%以内の当たり　1マス＝1回", t_cap=Sk("c5_96", 0.0) - 1.05, t0=Sk("c5_96", 0.3), t1=Sk("c5_96", 0.3) + 2.2,
                     t_count=Sk("c5_96", 0.55), count_fmt="1万回のうち {wins:,}回", seed=31)


def h1c(ctx, t):
    def extra(ctx, t, H, band, af):
        pass
    L_hist(ctx, t, H_WIDE["S2"], "g1_2", crit10, S("ch1") + 0.3, true_t=0.0, ghost=H_WIDE["S1"].s, extra=extra)


def h3a(ctx, t):
    L_hist(ctx, t, H_NARROW["S3"], "g2_1", crit10, S("g2_1") - 0.6, true_t=S("g2_1") - 0.6)


def h3b(ctx, t):
    L_hist(ctx, t, H_NARROW["S3"], None, crit_sw, S("g2_2") - 0.2, k_full=10000, true_t=0.0)


def h4(ctx, t):
    L_hist(ctx, t, H_NARROW["S4"], "g3_1", crit5, S("g3_1") - 0.6, true_t=S("g3_1") - 0.6)


def h5(ctx, t):
    L_hist(ctx, t, H_NARROW["S5"], "g3_2", crit5, S("g3_2") - 0.6, true_t=S("g3_2") - 0.6)


layer("earthA", 0.0, Sk("c0_stick") - 0.25, L_earthA, fi=0.0)
layer("ang", Sk("c0_stick") - 0.25, Sk("c0_360") - 0.25, L_ang)
layer("circ", Sk("c0_360") - 0.25, Sk("c0_why") - 0.25, L_circ)
layer("earthB", Sk("c0_why") - 0.25, Sk("c0_800") - 0.4, L_earthB)
layer("ring", Sk("c0_800") - 0.4, S("ch1") + 0.1, L_ring)
layer("h1_frame", S("ch1") + 0.1, Sk("c1_stick") - 0.45, h1_frame)
layer("stickfig", Sk("c1_stick") - 0.45, S("g1_1"), L_stickfig)
layer("h1_grow", S("g1_1"), Sk("c1_hit") - 1.2, h1_grow)
layer("grid1", Sk("c1_hit") - 1.2, Sk("c1_add") - 0.2, lambda ctx, t: GRID1.draw(ctx, t))
layer("stick10", Sk("c1_add") - 0.2, S("g1_2"), L_stick10)
layer("h1c", S("g1_2"), Sk("c2_dist") - 0.5, h1c)
layer("dist2", Sk("c2_dist") - 0.5, S("g2_1"), L_dist2)
layer("h3a", S("g2_1"), Sk("c2_break") - 1.6, h3a)
layer("brk", Sk("c2_break") - 1.6, S("g2_2"), L_break)
layer("h3b", S("g2_2"), Sk("c3_add10") - 0.5, h3b)
layer("days", Sk("c3_add10") - 0.5, S("g3_1"), L_days)
layer("h4", S("g3_1"), Sk("c3_habit") - 0.6, h4)
layer("tip", Sk("c3_habit") - 0.6, S("g3_2"), L_tip)
layer("h5", S("g3_2"), S("ch4") + 0.1, h5)
layer("ruler", S("ch4") + 0.1, Sk("c4_lat") - 0.45, L_ruler)
layer("lat", Sk("c4_lat") - 0.45, Sk("c4_sun") - 0.45, L_lat)
layer("sunoff", Sk("c4_sun") - 0.45, Sk("c4_pos") - 0.45, L_sunoff)
layer("map4", Sk("c4_pos") - 0.45, S("ch5") + 0.1, L_map4)
layer("near1", S("ch5") + 0.1, Sk("c5_fine") - 0.9, L_near1)
layer("near", Sk("c5_fine") - 0.9, Sk("c5_96") - 1.2, L_near)
layer("grid5", Sk("c5_96") - 1.2, S("ch6") + 0.1, lambda ctx, t: GRID5.draw(ctx, t))
layer("stad", S("ch6") + 0.1, S("ch7") + 0.1, L_stad)
layer("summ", S("ch7") + 0.1, T_ES + 0.8, L_summ)

LAYER_OUT, LAYER_IN, LAYER_DELAY = 0.2, 0.25, 0.2


def draw_left(ctx, t):
    for name, t0, t1, fn, fi, fo in LAYERS:
        fo = min(fo, LAYER_OUT)
        if t < t0 - 1e-6 or t > t1 + fo:
            continue
        a_in = 1.0 if fi <= 0 else ease_out(clamp01((t - t0 - LAYER_DELAY) / LAYER_IN))
        a = a_in * (1.0 if fo <= 0 else 1 - clamp01((t - t1) / fo))
        ctx.save()
        clip_left(ctx)
        grp(ctx, a, fn, t)
        ctx.restore()


# ============================================================
# 右ページ
# ============================================================
def stk(ctx, t, key, s, y, color="yellow", fg=INK, a=1.0, size=44, tilt=-0.012, off=0.3, x=RX, frac=0.0, until=None):
    """右ページの付せん。台本の文（手がかり key）から現れる。until を過ぎると消える"""
    t0 = Sk(key, frac) + off
    if t < t0:
        return 0, 0
    al = a * fade(t, t0)
    if until is not None:
        al *= out_fade(t, until, 0.3)
    return mini_sticky(ctx, s, x, y, size, color, fg=fg, a=al, align="left", tilt=tilt)


QLINES = ["2200年前の", "人は、棒1本で", "地球の大きさを", "当てた？"]
QTXT = "".join(QLINES)                                   # 題名・サムネと同じ言葉
QSMALL = "2200年前の人は、棒1本で\n地球の大きさを当てた？"
T_SHRINK = Sk("c0_era", 0.2)
T_OPEN = Sk("c0_x50", 0.62)                              # 答えの箱が「約4万km」に開く（声が「4万km」と言う）
T_UP1 = 3.1
HIDE_AT = 3.2


class ChikyuTeaser(lk.OpeningTeaser):
    """冒頭の答えの箱「地球一周 ？km」: 数字が0から上がり、4万の手前で「？」に伏せ、「800kmの50倍で、4万km」で「約4万km」に開く"""

    def draw_box(self, ctx, t, a=1.0):
        al = a * (lk._out_fade(t, self.t_out, 0.4) if self.t_out is not None else 1.0)
        if al <= 0.003:
            return
        x0, y0, x1, y1 = self.box
        ctx.set_source_rgba(1, 1, 1, 0.6 * al)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * al))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        cy = (y0 + y1) / 2
        text(ctx, self.box_title, x0 + 30, cy, self.title_size, INK, align="left", alpha=al)
        if t >= T_OPEN:
            u = lk._fade(t, T_OPEN, 0.5)
            text(ctx, "約4万km", x1 - 30, cy, self.val_size, RED, align="right", alpha=al * u)
        elif t >= self.hide_at:
            text(ctx, "？km", x1 - 30, cy, self.val_size, RED, align="right", alpha=al)
        else:
            v = self.value_at(t)
            text(ctx, f"{int(v // 100 * 100):,}km", x1 - 30, cy, self.val_size, self.color, align="right", alpha=al * lk._fade(t, 0.1, 0.25))


teaser = ChikyuTeaser(QLINES, left=None, thumb_text=QTXT, q_pos=(1050, 300), q_size=96, box=(1030, 560, 1830, 704), box_title="地球一周", unit="km",
                      peak=36000.0, vmax=50000.0, t_up0=0.0, t_up1=T_UP1, hide_at=HIDE_AT, t_out=T_BOX_OUT, title_size=56, val_size=76, color=BLUE)

COND_ROWS = [("夏至の正午", "c0_ge", 0.2, 300), ("南の町は、影がほとんどできない", "c0_south", 0.1, 352), ("北の町は、影が斜めに伸びる", "c0_north", 0.1, 404),
             ("2つの町の距離 ＋ 影の角度\n→ 地球一周", "c0_why", 0.45, 474)]


def cond_sticky(ctx, t):
    t0 = Sk("c0_cond", 0.3)
    a = fade(t, t0, 0.4) * out_fade(t, T_BOX_OUT - 0.1, 0.3)
    if a <= 0.003:
        return
    ctx.save()
    ctx.translate(RX - 12 + 395, 205 + 167)
    ctx.rotate(-0.006)
    ctx.translate(-(RX - 12 + 395), -(205 + 167))
    ctx.set_source_rgba(0.15, 0.13, 0.08, 0.16 * a)
    rrect(ctx, RX - 12 + 5, 205 + 8, 790, 335, 6)
    ctx.fill()
    fill(ctx, hexrgb(STICKY["yellow"], a))
    rrect(ctx, RX - 12, 205, 790, 335, 6)
    ctx.fill()
    ctx.set_source_rgba(1, 1, 1, 0.35 * a)
    ctx.rectangle(RX - 12, 205, 790, 12)
    ctx.fill()
    text(ctx, "条件", RX + 20, 245, 44, RED, align="left", alpha=a)
    for s_, key, fr, yy in COND_ROWS:
        wr(ctx, s_, RX + 20, yy, 42, INK, Sk(key, fr), t, align="left", alpha=a)
    ctx.restore()


def R_ch0(ctx, t):
    big = out_fade(t, T_SHRINK - 0.2, 0.2)
    teaser.draw_question(ctx, t, big)
    small = fade(t, T_SHRINK + 0.05, 0.2) * out_fade(t, S("ch1") - 0.2, 0.2)
    if small > 0.003:
        text(ctx, QSMALL, RX, 100, 56, INK, align="left", alpha=small)
    teaser.draw_box(ctx, t)
    t_off = Sk("c0_cond", 0.0) - 0.15
    if t >= Sk("c0_10k", 0.35) and t < t_off + 0.4:
        a = fade(t, Sk("c0_10k", 0.35), 0.3) * out_fade(t, t_off, 0.3)
        sticky(ctx, "1万回", RX + 135, 275, 64, "pink", fg=RED, a=a, tilt=-0.02)
        mini_sticky(ctx, "測るたびに少しぶれる", RX, 385, 44, "mint", a=a * fade(t, Sk("c0_10k", 0.6), 0.3), align="left", tilt=-0.01)
    cond_sticky(ctx, t)
    t_out = T_BOX_OUT - 0.1
    w1, _ = stk(ctx, t, "c0_72", "7.2度", 775, "pink", fg=RED, size=64, tilt=-0.015, off=0.3, until=t_out)
    stk(ctx, t, "c0_50", "360 ÷ 7.2 ＝ 50", 775, "mint", size=52, tilt=0.01, off=0.5, x=RX + 340, until=t_out)
    stk(ctx, t, "c0_800", "約800km", 880, "yellow", size=52, tilt=-0.01, off=0.3, until=t_out)


def R_ch1(ctx, t):
    stk(ctx, t, "c1_base", "当たり ＝\n本当の値から10%以内", 165, "yellow", size=48, tilt=-0.012, off=0.2)
    stk(ctx, t, "c1_read", "読み取り 1.5cm", 300, "pink", fg=RED, size=50, tilt=0.012, off=0.2)
    stk(ctx, t, "c1_read", "ぶれの大きさはこの動画の条件", 388, "mint", size=40, tilt=-0.008, off=1.2)
    stk(ctx, t, "c1_dist", "距離のぶれ 10%", 478, "pink", fg=RED, size=50, tilt=-0.012, off=0.2)


def R_ch2(ctx, t):
    stk(ctx, t, "c2_2pct", "距離のぶれ\n10% → 2%", 160, "pink", fg=RED, size=50, tilt=-0.012, off=0.2, until=Sk("c2_zure", 0.0) - 0.2)
    stk(ctx, t, "c2_2pct", "たとえば、きちんと測れたら", 262, "mint", size=40, tilt=0.008, off=1.0, until=Sk("c2_zure", 0.0) - 0.2)
    stk(ctx, t, "c2_prop", "地球一周 ＝\n距離 × 360 ÷ 影の角度", 400, "yellow", size=46, tilt=-0.01, off=0.3, until=Sk("c2_strict", 0.0) - 0.2)
    stk(ctx, t, "c2_zure", "ずれ", 150, "pink", fg=RED, size=56, tilt=0.012, off=0.3)
    stk(ctx, t, "c2_mid", "ずれの中央値", 250, "yellow", size=56, tilt=-0.012, off=0.3, frac=0.55)


def R_ch3(ctx, t):
    stk(ctx, t, "c3_habit", "ぼやけ → 読む位置の癖", 160, "yellow", size=46, tilt=-0.012, off=0.5)
    stk(ctx, t, "c3_always", "癖は毎日同じ", 255, "pink", fg=RED, size=54, tilt=0.012, off=0.3)


def R_ch4(ctx, t):
    stk(ctx, t, "c4_16", "＋1.6%", 160, "pink", fg=RED, size=72, tilt=-0.015, off=0.3, frac=0.2)


def R_ch5(ctx, t):
    stk(ctx, t, "c5_100", "町の距離 100km", 160, "pink", fg=RED, size=56, tilt=-0.012, off=0.2)


def R_ch6(ctx, t):
    stk(ctx, t, "c6_25", "250,000スタディオン", 140, "yellow", size=52, tilt=-0.012, off=0.3, frac=0.4, until=S("ch7") - 0.6)
    stk(ctx, t, "c6_252", "252,000", 245, "yellow", size=52, tilt=0.012, off=0.3, frac=0.4, until=S("ch7") - 0.6)
    stk(ctx, t, "c6_len", "1スタディオン ＝ ？m", 350, "mint", fg=RED, size=52, tilt=-0.01, off=0.2, until=S("ch7") - 0.6)


def R_ch7(ctx, t):
    pass


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


# ============================================================
# 梯子・棒の枠（右ページ）
# ============================================================
LAD_LABELS = ["棒1m・目で読む", "棒を10mに", "距離をきちんと", "10日の平均", "影の先をくっきり"]
LAD_NAMES = ["棒1m・目で読む", "＋棒を10mに", "＋距離をきちんと", "＋10日の平均", "＋影の先をくっきり"]
V_L = [STEP["S1"]["w10"], STEP["S2"]["w10"], STEP["S3"]["w10"], STEP["S4"]["w5"], STEP["S5"]["w5"]]       # 梯子の値（段1〜3は±10%、段4・5は±5%）
V_T = [pc(V_L[0]), pc(V_L[1]), f"{STEP['S3']['w10'] * 100:.1f}%", pc(V_L[3]), pc(V_L[4])]
LAD_COL = [BLUE, BLUE, BLUE, ORANGE, ORANGE]
BELLS = []

T_LAD = Sk("c0_move", 0.0) + 0.5                          # 梯子の枠が出る
T_LV = [Sk("c1_hit", 0.55), Sk("c1_hit2", 0.55), Sk("c2_99", 0.5), Sk("c3_86", 0.55), Sk("c3_95", 0.55)]
L_LINE = [ID["c1_hit"], ID["c1_hit2"], ID["c2_99"], ID["c3_86"], ID["c3_95"]]
L_NAME_LINE = [ID["c1_stick"], ID["c1_add"], ID["c2_add"], ID["c3_add10"], ID["c3_add2"]]
MAIN_ROWS = [lk.Row(LAD_LABELS[i], V_L[i], t_label=T_LAD + 0.45 + 0.1 * i, t_value=T_LV[i], color=LAD_COL[i], line=L_LINE[i], text=V_T[i]) for i in range(5)]
MAIN = lk.LadderPanel("当たりの割合", MAIN_ROWS, box=(1000, 560, 1860, 920), t_frame=T_LAD, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4,
                      title_line=ID["c1_stick"])
BELLS += T_LV
# 名札の合図（名札は各段の文の頭より前に出ている＝枠は声の前）
MAIN_NAME_CUES = [lk.Cue(f"主な梯子 名札「{LAD_NAMES[i]}」", "frame", MAIN_ROWS[i].t_label, MAIN_ROWS[i].t_label + 0.4, L_NAME_LINE[i]) for i in range(5)]

# 基準の札（10%以内 → 1秒の場面の切り替えで 5%以内）
T_CRIT = Sk("c1_base", 0.0) - 1.0
T_CRIT5 = SW + 0.2
CRIT_CUES = [lk.Cue("基準の札「10%以内」", "frame", T_CRIT, T_CRIT + 0.4, ID["c1_base"]),
             lk.Cue("基準の札「5%以内」", "frame", T_CRIT5, T_CRIT5 + 0.25, ID["c2_5pct"])]


def crit_tag(ctx, t, a=1.0):
    a10 = fade(t, T_CRIT, 0.4) * out_fade(t, SW, 0.2)
    a5 = fade(t, T_CRIT5, 0.25)
    mini_sticky(ctx, "10%以内", 1700, 584, 42, "yellow", fg=RED, a=a * a10, tilt=-0.015)
    mini_sticky(ctx, "5%以内", 1700, 584, 42, "pink", fg=RED, a=a * a5, tilt=0.015)


T_M84 = Sk("c2_84", 0.8)
M84_CUE = lk.Cue("棒の上の細い印 84", "value", T_M84, T_M84 + 0.4, ID["c2_84"])


def mark84(ctx, t, a=1.0):
    al = a * fade(t, T_M84, 0.4)
    if al <= 0.003:
        return
    g = MAIN.layout()
    y = g["ys"][2]
    bh = g["bar_h"]
    x = g["track_x"] + g["track_w"] * STEP["S3"]["w5"]
    line2(ctx, (x, y - bh / 2 - 7), (x, y + bh / 2 + 7), INK, 5, al, cap=cairo.LINE_CAP_BUTT)
    text(ctx, f"{pc(STEP['S3']['w5'])[:-1]}", x - 10, y, 40, "#ffffff", align="right", alpha=al)


def draw_main(ctx, t, a):
    MAIN.draw(ctx, t, a)
    crit_tag(ctx, t, a * fade(t, T_LAD, 0.4))
    mark84(ctx, t, a)


# ずれの中央値（第2章・第3章）
def mk_pair(title, rows, t_frame, line_title):
    return lk.LadderPanel(title, rows, box=(1000, 330, 1860, 545), t_frame=t_frame, vmax=0.12, label_size=40, val_size=48, title_size=44, fade=0.4, title_line=line_title)


T_P2 = Sk("c2_mid", 0.0) - 1.5
P2 = mk_pair("ずれの中央値", [
    lk.Row("棒1m・目で読む", STEP["S1"]["mad"], t_label=T_P2 + 0.1, t_value=Sk("c2_res", 0.55), color=RED, line=ID["c2_res"], text="約10%"),
    lk.Row("距離をきちんと", STEP["S3"]["mad"], t_label=T_P2 + 0.2, t_value=Sk("c2_mid", 0.8), color=ORANGE, line=ID["c2_mid"], text="約2%")], T_P2, ID["c2_mid"])
T_P3 = Sk("c3_mad", 0.0) - 1.5
P3 = mk_pair("ずれの中央値", [
    lk.Row("＋10日の平均", STEP["S4"]["mad"], t_label=T_P3 + 0.1, t_value=Sk("c3_mad", 0.25), color=ORANGE, line=ID["c3_mad"], text="約2%"),
    lk.Row("影の先をくっきり", STEP["S5"]["mad"], t_label=T_P3 + 0.2, t_value=Sk("c3_mad", 0.65), color=GREEN, line=ID["c3_mad"], text="1.8%")], T_P3, ID["c3_mad"])
BELLS += [Sk("c2_mid", 0.8), Sk("c3_mad", 0.65)]


class StackBars:
    """第4章の2本: 名札を上に1行、棒をその下に（名札が長いので横並びにしない）"""

    def __init__(self, title, rows, box, t_frame, vmax, title_line):
        self.title, self.rows, self.box, self.t_frame, self.vmax, self.title_line = title, rows, box, t_frame, vmax, title_line

    def draw(self, ctx, t, a=1.0):
        x0, y0, x1, y1 = self.box
        af = a * fade(t, self.t_frame, 0.4)
        if af <= 0.003:
            return
        ctx.set_source_rgba(1, 1, 1, 0.6 * af)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * af))
        ctx.set_line_width(3)
        rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
        ctx.stroke()
        text(ctx, self.title, x0 + 32, y0 + 38, 44, INK, align="left", alpha=af)
        tx, tw = x0 + 32, (x1 - 32) - (x0 + 32) - 250
        for i, r in enumerate(self.rows):
            yl = y0 + 118 + i * 140
            yb = yl + 58
            la = a * fade(t, r["t_label"], 0.4)
            if la <= 0.003:
                continue
            text(ctx, r["label"], tx, yl, 44, INK, align="left", alpha=la)
            ctx.set_source_rgba(1, 1, 1, 0.7 * la)
            rrect(ctx, tx, yb - 20, tw, 40, 6)
            ctx.fill()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.8 * la))
            ctx.set_line_width(2.5)
            rrect(ctx, tx, yb - 20, tw, 40, 6)
            ctx.stroke()
            bu = ease_out(clamp01((t - r["t_value"]) / 0.9))
            if bu > 0.003:
                ctx.set_source_rgba(*hexrgb(r["color"], 0.92 * la))
                rrect(ctx, tx, yb - 20, max(4.0, tw * r["value"] / self.vmax) * bu, 40, 6)
                ctx.fill()
                if bu > 0.15:
                    text(ctx, r["text"], x1 - 28, yb, 48, r["color"], align="right", alpha=la * clamp01((bu - 0.15) / 0.3))

    def cues(self):
        out = [lk.Cue(f"{self.title} 枠", "frame", self.t_frame, self.t_frame + 0.4, self.title_line)]
        for r in self.rows:
            out.append(lk.Cue(f"{self.title} 名札「{r['label']}」", "frame", r["t_label"], r["t_label"] + 0.4, r["line"]))
            out.append(lk.Cue(f"{self.title} 棒「{r['label']}」", "value", r["t_value"], r["t_value"] + 0.9, r["line"]))
        return out


T4 = S("ch4") + 0.35
P4 = StackBars("地球一周の答え（測りまちがいなし）", [
    dict(label="エラトステネスの考え方", value=CONST["no_err"], text=f"{ihalf(CONST['no_err']):,}km", color=ORANGE, t_label=Sk("c4_632", 0.0) - 1.0, t_value=Sk("c4_632", 0.7), line=ID["c4_632"]),
    dict(label="正しい計算", value=CONST["correct"], text=f"{ihalf(CONST['correct']):,}km", color=BLUE, t_label=Sk("c4_cor", 0.0) - 1.0, t_value=Sk("c4_cor", 0.7), line=ID["c4_cor"])],
    (1000, 560, 1860, 920), T4, 45000.0, ID["c4_632"])
BELLS += [Sk("c4_632", 0.7), Sk("c4_cor", 0.7)]

T5 = S("ch5") + 0.35
T_CRIT_5 = Sk("c5_crit", 0.0) - 1.0
P5_ROWS = [lk.Row("棒1m・目で読む", NEAR_C[100]["w10"], t_label=Sk("c5_8", 0.0) - 1.0, t_value=Sk("c5_8", 0.72), color=RED, line=ID["c5_8"], text=f"{NEAR_C[100]['w10'] * 100:.1f}%"),
           lk.Row("影の先をくっきり", NEAR_F[100]["w10"], t_label=Sk("c5_fine", 0.0) - 1.0, t_value=Sk("c5_96", 0.5), color=GREEN, line=ID["c5_96"], text=pc(NEAR_F[100]["w10"])),
           lk.Row("800kmの町", STEP["S1"]["w10"], t_label=Sk("c5_800", 0.0) - 1.0, t_value=Sk("c5_48", 0.6), color=ORANGE, line=ID["c5_48"], text=pc(STEP["S1"]["w10"]), branch=True)]
P5 = lk.LadderPanel("町が100kmのとき", P5_ROWS, box=(1000, 560, 1860, 920), t_frame=T5, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4, title_line=ID["c5_8"])
P5_CRIT_CUE = lk.Cue("基準の札「10%以内」(第5章)", "frame", T_CRIT_5, T_CRIT_5 + 0.4, ID["c5_crit"])
BELLS += [Sk("c5_8", 0.72), Sk("c5_96", 0.5), Sk("c5_48", 0.6)]

T6 = S("ch6") + 0.35
P6_ROWS = [lk.Row("157.5mなら", CONST["stadion_157"] / 50000.0, t_label=Sk("c6_157", 0.0) - 1.0, t_value=Sk("c6_157", 0.62), color=BLUE, line=ID["c6_157"], text="約3.9万km"),
           lk.Row("185mなら", CONST["stadion_185"] / 50000.0, t_label=Sk("c6_185", 0.0) - 1.0, t_value=Sk("c6_185", 0.5), color=ORANGE, line=ID["c6_185"], text="約4.6万km"),
           lk.Row("本当の値", CONST["c_true"] / 50000.0, t_label=Sk("c6_157", 0.0) - 1.0, t_value=Sk("c6_157", 0.0) - 1.0, color=RED, plain=True, branch=True, text="約4万km")]
P6 = lk.LadderPanel("25万スタディオン", P6_ROWS, box=(1000, 560, 1860, 920), t_frame=T6, vmax=1.0, label_size=40, val_size=48, title_size=44, fade=0.4, title_line=ID["c6_157"], plus=False, arrows=False)
BELLS += [Sk("c6_157", 0.62), Sk("c6_185", 0.5)]

# まとめ: 5本の棒を右ページいっぱいに
T7 = S("ch7") + 0.3
SUM_SUB = ["10%以内", None, None, "ここから 5%以内", None]
SUM_T = [Sk("c7_0", 0.04), Sk("c7_0", 0.2), Sk("c7_0", 0.36), Sk("c7_0", 0.52), Sk("c7_0", 0.68)]
SUM_ROWS = [lk.Row(LAD_LABELS[i], V_L[i], t_label=T7 + 0.05 + 0.03 * i, t_value=SUM_T[i], color=LAD_COL[i], line=(ID["c7_0"] if i in (0, 2) else None),
                   text=V_T[i], sub=SUM_SUB[i]) for i in range(5)]
SUMP = lk.LadderPanel("当たりの割合", SUM_ROWS, box=(1000, 100, 1860, 900), t_frame=T7, vmax=1.0, label_size=44, val_size=52, title_size=48, sub_size=40, fade=0.3,
                      title_line=ID["c7_0"])
BELLS += SUM_T


def draw_panel(ctx, t):
    a_all = out_fade(t, T_ES, 0.4)
    grp(ctx, a_all * out_fade(t, S("ch4") - 0.1, 0.2), draw_main, t, 1.0)
    grp(ctx, a_all * out_fade(t, S("ch3") + 0.0, 0.3), lambda c, t_: P2.draw(c, t_), t)
    grp(ctx, a_all * out_fade(t, S("ch4") - 0.1, 0.2), lambda c, t_: P3.draw(c, t_), t)
    grp(ctx, a_all * out_fade(t, S("ch5") - 0.0, 0.25), lambda c, t_: P4.draw(c, t_), t)
    grp(ctx, a_all * out_fade(t, S("ch6") - 0.0, 0.25), draw_p5, t)
    grp(ctx, a_all * out_fade(t, S("ch7") - 0.0, 0.25), lambda c, t_: P6.draw(c, t_), t)
    grp(ctx, a_all, lambda c, t_: SUMP.draw(c, t_), t)


def draw_p5(ctx, t):
    P5.draw(ctx, t)
    a = fade(t, T_CRIT_5, 0.4)
    mini_sticky(ctx, "10%以内", 1700, 584, 42, "yellow", fg=RED, a=a, tilt=-0.015)


ALL_CUES = (MAIN.cues() + MAIN_NAME_CUES + CRIT_CUES + [M84_CUE] + P2.cues() + P3.cues() + P4.cues() + P5.cues() + [P5_CRIT_CUE] + P6.cues() + SUMP.cues()
            + BREAK.cues() + GRID1.cues(ID["c1_hit"], ID["c1_hit"]) + GRID5.cues(ID["c5_96"], ID["c5_96"])
            + [lk.Cue("答えの箱「約4万km」", "value", T_OPEN, T_OPEN + 0.5, ID["c0_x50"])])
# 梯子の枠の記録は「声の文の頭 − 0.5秒以前」。第6章の「本当の値」の棒は答えではなく枠（最初から見える）


# ============================================================
# 章カード・終了画面・全体
# ============================================================
END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"
LCX_E, RCX_E = 490, 1430


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
    return [("棒1m・目で読むと", f"100回に{ihalf(V_L[0] * 100)}回", "yellow", INK, -0.010),
            ("町の距離をきちんと測ると", "100回に99回を超える", "pink", RED, 0.008),
            ("大事なのは", "影より、町の距離", "mint", INK, -0.008)]


def end_screen(ctx, t):
    t0 = T_ES
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "棒1本と影で、地球の大きさを、1万回 測ったら", LCX_E, 162, 40, INK, bold=False, alpha=b)
    H_, GAP_, Y0_ = 215, 22, 212
    for k, (lab, val, col, fg, tilt) in enumerate(end_rows()):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt, lsz=44, vsz=60)
    t9 = Sk("c7_ch", 0.0)
    q = fade(t, t0 + 0.6, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
    if q > 0.003:
        sticky(ctx, "あなたなら、\n2つの町の距離を\nどう測りますか？", RCX_E, 480, 52, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


CARD_DELAY, CARD_HOLD = 0.4, 2.2                    # 章カードは章の頭から0.4秒あとに出て、約2.6秒まで（前の章の付せんが消えてから）
CARD_POS = {4: (960, 130), 6: (960, 420), 7: (480, 650)}   # 題が長い第4・6章は見開きの上・まとめは左ページの下（右ページは梯子が上まで埋まる）。ほかの章は右ページの上
CARD_POS_DEFAULT = (1425, 300)


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1] - CARD_DELAY
        if 0 <= age <= CARD_HOLD:
            a = clamp01(age / 0.3) * clamp01((CARD_HOLD - age) / 0.4)
            cx_, cy_ = CARD_POS.get(ch[0], CARD_POS_DEFAULT)
            lf.chapter_card(ctx, CARD_TITLES[ch[0]], a, x=cx_, y=cy_, size=60)


def pages(ctx, t):
    draw_left(ctx, t)
    draw_right(ctx, t)
    draw_panel(ctx, t)
    overlays(ctx, t)


# ============================================================
# 区切り（第3章と第4章のあいだ・声なし約4秒）。engine/longkit.py の Eyecatch。
#   見開きの左ページに「ここまで」＋左向きの赤い矢印＋2行、右ページに「ここから」＋右向きの赤い矢印＋2行。カメが左から右へ歩く。
#   章ではない（chapters に入らない）。前の章の付せん・梯子などは、区切りの間は描かない（Eyecatch が自前の紙を敷く）。
# ============================================================
EC_IDS = [g for g in sorted(GAP_NOTE) if "区切り" in GAP_NOTE[g]]
if len(EC_IDS) != 1:
    raise SystemExit("台本に「（無音 4秒・区切り。…）」の行が1つだけ必要です（第3章の終わり）: " + str(EC_IDS))
EC_ID = EC_IDS[0]
T_EC0, T_EC1 = S(EC_ID), E(EC_ID)
EC = lk.Eyecatch(T_EC0, ("効くのは、", "町の距離"), ("昔の考え方は？", "町が近かったら？"), dur=T_EC1 - T_EC0)


def footstep(freq, dur_=0.11):
    """カメの足音（ぽてっ）: 少し下がる短い音＋やわらかい当たり（escalator-long.py と同じ）"""
    t_ = core._t(dur_)
    f = freq * (1 + 0.5 * np.exp(-t_ * 55))
    body = np.sin(2 * np.pi * np.cumsum(f) / core.SR) * np.exp(-t_ * 38) * np.minimum(1, t_ * 900)
    rng = np.random.default_rng(int(freq))
    tap = np.convolve(rng.standard_normal(len(t_)), np.ones(12) / 12, mode="same") * np.exp(-t_ * 160) * 0.6
    return body + tap


def draw(ctx, t):
    lf.spread(ctx)
    if T_EC0 <= t < T_EC1 + 0.35:                         # 区切りの間（消えきるまで）は Eyecatch だけ。章カード（章の頭から0.4秒あと）とは重ならない
        EC.draw(ctx, t)
        lf.subtitle(ctx, t, tl)
        return
    if t < T_ES + 0.6:
        grp(ctx, 1 - fade(t, T_ES, 0.5), pages, t)
    if t >= T_ES:
        end_screen(ctx, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。効果音は章の始まり・棒が伸びるとき・早回し）
# ============================================================
def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 8):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    rng_f = np.random.default_rng(21)                   # 区切り: 足あとの点が出るたびに、カメの足音（高さを少しずつ変える）
    for k_, ts_ in enumerate(EC.step_times()):
        mx.add(ts_, footstep((420.0 if k_ % 2 else 520.0) * float(rng_f.uniform(0.9, 1.12))), 0.32)
    for g in sorted(GAP_NOTE):
        if g == EC_ID:
            continue                                     # 区切りは早回しではない（拍・きらめきなし）
        if GAP_SEC[g] >= 2.0:
            beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
            mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
        else:
            mx.add(S(g) + 0.05, tick(1400, 0.05), 0.3)
    for k_, tt in enumerate(sorted(BELLS)):
        mx.add(tt + 0.3, bell(659.3 if k_ % 2 else 784.0, 1.0), 0.3)
    mx.add(T_OPEN + 0.1, chord([293.7, 370.0, 440.0], 1.6), 0.4)
    mx.add(Sk("c7_4", 0.05), chord([293.7, 370.0, 440.0], 1.6), 0.45)
    mx.add(Sk("c7_ch", 0.0) + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画（--fake-voice の時刻で）
# ============================================================
def still_list():
    return [
        ("01_0.0s", "① 0.0秒: 問い（サムネと同じ言葉）・2本の棒（片方は影が長い）・答えの箱", 0.0),
        ("02_2.5s", "② 2.5秒: 片方の影が縮み、もう片方が伸びる・数字が上がる", 2.5),
        ("03_5.0s", "③ 5.0秒: 南の棒の影は消えた・数字は「？」に伏せる", 5.0),
        ("04_ch0_geom", "④ 第0章: 断面図（光は南の棒と平行・中心の角＝影の角度）", Ek("c0_cen") + 0.4),
        ("05_ch0_x50", "⑤ 第0章: 50個の弧・箱が「約4万km」に開く", T_OPEN + 1.1),
        ("06_ch1_ans", "⑥ 第1章の答え: 100回に48回（1万マス）", Ek("c1_hit") + 0.5),
        ("07_ch2_ans", "⑦ 第2章の答え: 100回のうち99回を超える（10%以内）", Sk("c2_99", 0.5) + 2.2),
        ("08_sw_before", "⑧ 基準の切り替え 前（10%以内）", SW - 0.12),
        ("09_sw_after", "⑨ 基準の切り替え 後（5%以内・細い印84）", Ek("c2_84") + 0.5),
        ("10_ch3_ans", "⑩ 第3章の答え: 95・ずれの中央値 約2% → 1.8%", Ek("c3_mad") + 0.5),
        ("10b_eye_start", "⑱ 区切り 始め: 「ここまで」「ここから」・赤い矢印・カメが左ページ（前の章の絵は片づいた）", EC.still_times()[0]),
        ("10c_eye_mid", "⑲ 区切り 途中: カメが真ん中あたりを歩く・足あと", EC.still_times()[1]),
        ("10d_eye_end", "⑳ 区切り 終わり: カメが右ページへ着く", EC.still_times()[2]),
        ("11_ch4_sun", "⑪ 第4章: 太陽の向き0.4度 → 一周は小さく出る", Ek("c4_small") - 0.5),
        ("12_ch4_map", "⑫ 第4章: 町の並び 844km と 790km", Ek("c4_844b") + 0.6),
        ("13_ch5_ans", "⑬ 第5章: 地球の弧に2組の棒（800km=7.2度・100km=0.9度）・読み取りのぶれの帯に0.9度が埋もれる", Ek("c5_why") - 0.3),
        ("14_ch5_grid", "⑭ 第5章の答え: 丁寧な測り方 96（1万マス）", Ek("c5_96") + 0.5),
        ("15_ch6", "⑮ 第6章: 157.5m と 185m", Ek("c6_185") + 1.2),
        ("16_summary", "⑯ まとめ: 5本の棒・影より町の距離", Ek("c7_3") + 0.5),
        ("17_end", "⑰ 終了画面", min(DUR - 0.5, Sk("c7_sub", 0.0) + 1.0)),
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
    lab_h, pad = 34, 10
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
        dr.text((x + 4, y + H_ + 3), f"{k + 1}  {_ts(items[k][2])}", fill=(235, 235, 235), font=fnt)
    sheet.save(out_dir / "sheet_480.png")
    print("一覧:", out_dir / "sheet_480.png")


def stills_preview(out_dir):
    stills_sheet(out_dir, still_list())
    from PIL import Image                                  # 区切りの still_times() 3枚を幅480pxに縮めて横に並べる
    ims = [Image.open(out_dir / f"{n}.png").convert("RGB").resize((480, 270), Image.LANCZOS) for n in ("10b_eye_start", "10c_eye_mid", "10d_eye_end")]
    sh = Image.new("RGB", (480 * 3 + 16, 270), "white")
    for i, im in enumerate(ims):
        sh.paste(im, (i * 488, 0))
    sh.save(out_dir / "eyecatch_480.png")
    print("区切り3枚:", out_dir / "eyecatch_480.png")
    tm = [Sk("c1_med", 0.0) - 4.0, Ek("c1_med") + 0.3, Sk("c2_mid", 1.2), Ek("c3_mad") + 0.5]       # 「中央値」の定義・線の札・付せん「ずれの中央値」・第3章の棒
    ims = []
    for i, tt in enumerate(tm):
        pp = out_dir / f"_med_{i}.png"
        lf.still(draw, tt, pp)
        ims.append(Image.open(pp).convert("RGB").resize((480, 270), Image.LANCZOS))
        pp.unlink()
    sh = Image.new("RGB", (488 * 4 - 8, 270), "white")
    for i, im in enumerate(ims):
        sh.paste(im, (i * 488, 0))
    sh.save(out_dir / "median_480.png")
    print("中央値の場面:", out_dir / "median_480.png", [round(x, 1) for x in tm])


# ============================================================
# 文字起こし・読み
# ============================================================
def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字の問い・2本の棒と影・答えの箱）]")
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


# ============================================================
# 場面の照合
# ============================================================
NUM_RE = r"\d[\d,]*(?:\.\d+)?"
CARD_LINES = {ln for t_ in CARD_TITLES for ln in t_.split("\n")}


def _allowed_nums():
    ok = set(range(0, 13)) | {0.9, 0.5, 8.5, 25, 50, 99, 100, 360, 800, 600, 2200}
    ok |= {1.5, 7.2, 0.4, 1.6, 1.8, 3.6, 4.4, 3.9, 4.6, 157.5, 185, 844, 790, 40632, 40008, 250000, 252000}
    ok |= {float(ihalf(v * 100)) for v in V_L} | {round(STEP["S3"]["w10"] * 100, 1), float(ihalf(STEP["S3"]["w5"] * 100))}
    ok |= {float(ihalf(NEAR_C[100]["w10"] * 100)), float(ihalf(NEAR_F[100]["w10"] * 100)), float(ihalf(STEP["S1"]["w10"] * 100))}
    ok |= {float(STEP["S1"]["n10"]), float(NEAR_F[100]["n10"])}
    ok |= {float(ihalf(STEP["S1"]["mad"] * 100)), float(ihalf(STEP["S3"]["mad"] * 100))}
    return ok


def _split_pairs(pairs):
    return pairs


def first_seen(frames, pred):
    for f in frames:
        if any(pred(e[0], e) for e in f[1]):
            return f[0]
    return None


def motion_first_03():
    """0〜0.3秒で画面が動いているか（公開前チェックと同じ基準）"""
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


def scene_checks(frames=None):
    txt = lambda k: tl.clip(ID[k]).text
    checks = []

    def A(name, cond):
        checks.append((name, float(bool(cond)), 1.0, 0.0))

    def V(name, val, exp, tol):
        checks.append((name, float(val), float(exp), tol))
    # ---- 台本の読み込み ----
    A(f"台本: 章は8つ（0〜7）・どの章にも声の文がある・場面の合図 {len(ID)} か所がどれも1文に見つかる", len(CHAPS) == 8 and all(any(it[0] == "line" for it in c["items"]) for c in CHAPS))
    A("台本: 「- 」の行の文言を一字も変えずに読んでいる（声の文を並べ直すと台本の行と同じ。長い文だけ区切りで分けた）",
      "".join(LINES[i][1] for i in LINES) == "".join(it[1] for c in CHAPS for it in c["items"] if it[0] == "line"))
    nar_head = NARR_PATH.read_text(encoding="utf-8").splitlines()
    title_line = next(ln for ln in nar_head if ln.startswith("題名:"))
    A(f"題名「{QTXT}…」の言葉が台本の題名の行と画面の問いで同じ（サムネと同じ言葉にそろえる）", QTXT in title_line)
    V("台本: 声は 0.5秒から（0〜0.5秒は絵だけ）", S(ID["c0_q"]), 0.5, 1e-6)
    l0 = [it.id for it in tl.items if isinstance(it, lf.Line) and it.id.startswith("c0_")]
    gaps0 = [S(b) - E(a) for a, b in zip(l0, l0[1:]) if S(b) < 70]
    A(f"台本: 冒頭（0〜70秒）の文と文の間は 0.3秒前後（{min(gaps0):.2f}〜{max(gaps0):.2f}秒）・無音の「待ち」なし（最初の無音は第1章: {min(S(g) for g in GAP_NOTE):.1f}秒）",
      all(abs(g - 0.3) < 0.011 for g in gaps0) and min(S(g) for g in GAP_NOTE) > S("ch1"))
    fast = [g for g in GAP_NOTE if GAP_SEC[g] >= 2.0 and g != EC_ID]                 # 区切りは早回しではない（下で別に確かめる）
    A(f"台本: 無音の早回し {len(fast)} か所はどれも4秒以内（{[GAP_SEC[g] for g in fast]}）・基準の切り替えは1秒（{GAP_SEC['g2_2']}）", len(fast) == 5 and all(GAP_SEC[g] <= 4.0 for g in fast) and GAP_SEC["g2_2"] == 1.0)
    A(f"台本: 区切りは1か所・約4秒（{GAP_SEC[EC_ID]}秒）・第3章のあと第4章の前・声なし・章に数えない（章は{len(CHAPS)}つ）・動画のほぼ真ん中（{T_EC0 / DUR:.0%}）",
      len(EC_IDS) == 1 and abs(GAP_SEC[EC_ID] - 4.0) <= 0.5 and E(ID["c3_end"]) <= T_EC0 + 1e-9 and E(EC_ID) <= S("ch4") and EC_ID.startswith("g3_")
      and not any(T_EC0 <= S(it.id) < T_EC1 for it in tl.items if isinstance(it, lf.Line)) and len(CHAPS) == 8 and 0.35 <= T_EC0 / DUR <= 0.65
      and all(T_EC0 + 0.5 > t_ or t_ >= T_EC1 for t_, _ in tl.chapters) and EC.dur >= 3.5)
    nums40 = []
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            nums40 += _re.findall(r"\d+(?:\.\d+)?(?=年|万|度|つ|%|km)|[0-9]+", split_reading(it.text)[0])
    A(f"台本: 冒頭40秒の声の数字は3個以内（{sorted(set(nums40))}）", len(set(nums40)) <= 3)
    # ---- 声の数字 = data.json ----
    exp = [("c1_hit", f"100回に{pc(V_L[0])[:-1]}回"), ("c1_hit2", f"100回に{pc(V_L[1])[:-1]}回"), ("c2_99", "99回を超えます"), ("c2_84", f"100回に{pc(STEP['S3']['w5'])[:-1]}回"),
           ("c3_86", f"100回に{pc(V_L[3])[:-1]}回"), ("c3_95", f"100回に{pc(V_L[4])[:-1]}回"), ("c1_med", "4万600km"), ("c3_mad", f"{STEP['S5']['mad'] * 100:.1f}%"),
           ("c4_632", "4万632km"), ("c4_16", f"{CONST['no_err_pct'] * 100:.1f}%"), ("c4_844", f"{CONST['d_gc']:.0f}km"), ("c4_790", f"{CONST['d_mer']:.0f}km"),
           ("c5_8", "100回に8回"), ("c5_48", "100回に48回"), ("c5_96", f"100回に{pc(NEAR_F[100]['w10'])[:-1]}回"),
           ("c6_157", "約3万9千km"), ("c6_185", "約4万6千km")]
    bad_ = [(k, s_) for k, s_ in exp if s_ not in txt(k)]
    A(f"声の数字 {len(exp)} か所が data.json の値（四捨五入）と同じ: 食い違い {bad_}", not bad_)
    # ---- 冒頭 0〜5秒 ----
    g = geometry_checks()
    A(f"冒頭: 0秒目は 北の影 {g['a0']['n']:.1f}px（なし）・南の影 {g['a0']['s']:.1f}px（長い）→ 6秒目は 南の影 {g['a1']['s']:.2f}px（なし）・北の影 {g['a1']['n']:.1f}px（伸びた）",
      g["a0"]["n"] < 1e-6 < g["a0"]["s"] and g["a1"]["s"] < 1e-6 < g["a1"]["n"])
    ss, nn = [], []
    for k in range(0, 16):
        ps = sun_phi_a(k * 0.25)
        r = {}
        for nm, ph in (("s", PHI_S), ("n", PHI_N)):
            tip = cpt(VA, ph, VA[2] + STICK_A)
            h = ray_hit(VA, tip, ps)
            base = cpt(VA, ph, VA[2])
            r[nm] = math.hypot(h[0] - base[0], h[1] - base[1])
        ss.append(r["s"])
        nn.append(r["n"])
    A("冒頭: 0〜3.5秒で 南の棒の影は単調に縮んで0に・北の棒の影は単調に伸びる（0.25秒ごとに計算）", all(a >= b - 1e-9 for a, b in zip(ss, ss[1:])) and all(a <= b + 1e-9 for a, b in zip(nn, nn[1:])) and ss[-1] < 1e-6 and nn[-1] > 50)
    V("幾何: 太陽の光は南の棒（の延長）と厳密に平行（外積）", g["cross"], 0.0, 1e-12)
    V("幾何: 北の棒と太陽の向きの角 ＝ 2本の棒が地球の中心でつくる角（同位角・度）", g["ang_tip"], g["ang_cen"], 1e-9)
    V("幾何: 断面図で南の棒の影は0（棒が光と重なる）", g["shadow_s"], 0.0, 1e-6)
    A(f"幾何: 断面図で北の棒の影が伸びる（{g['shadow_n']:.1f}px）", g["shadow_n"] > 20)
    V("幾何: 描いた中心角（度）＝ 棒の間の角（30度に大きく描く。本当は 7.2度で、「角度は大きく描いてあります」と画面に書く）", g["ang_cen"], 30.0, 1e-9)
    A(f"冒頭: 0〜0.3秒で画面が動く（変化 {motion_first_03():.3%} ≧ 0.15%）", motion_first_03() >= 0.0015)
    # ---- 梯子 ----
    A("梯子の名札は台本どおり: " + "・".join(f"「{MAIN.label_of(i)}」" for i in range(5)), [MAIN.label_of(i) for i in range(5)] == LAD_NAMES)
    A("梯子の値の文字は data.json（48・66・99.7・86・95）", V_T == [f"{ihalf(STEP['S1']['w10'] * 100)}%", f"{ihalf(STEP['S2']['w10'] * 100)}%", "99.7%", f"{ihalf(STEP['S4']['w5'] * 100)}%", f"{ihalf(STEP['S5']['w5'] * 100)}%"])
    A("梯子の棒の長さ ＝ 値（0〜100%）・棒1m<10m<距離<…（±10%の段は単調）", all(0 < v <= 1 for v in V_L) and V_L[0] < V_L[1] < V_L[2])
    probs = MAIN.layout_problems() + SUMP.layout_problems() + P5.layout_problems() + P6.layout_problems() + BREAK.layout_problems() + P2.layout_problems() + P3.layout_problems()
    A(f"梯子の配置の問題: {probs}", not probs)
    A("基準の札: 10%以内 → 5%以内（切り替えは 1秒の場面の中で 0.45秒までに完了＝次の文の頭の 0.5秒前）", T_CRIT5 + 0.25 <= S(ID["c2_5pct"]) - 0.5 + 1e-9 and abs(S(ID["c2_5pct"]) - E("g2_2")) < 1e-6)
    # ---- 絵は声より先に・答えは声に合わせて ----
    rows_, bad = lk.visual_lag(ALL_CUES, tl)
    lk.write_visual_lag_md(OUT / "visual_lag.md", rows_, bad)
    A(f"visual_lag: 合図 {len(rows_)} 件・枠が声の0.5秒前までにそろわないもの {len(bad)} 件（最も先: {min(r[3] for r in rows_):+.1f}秒）{[b[0] for b in bad[:3]]}", not bad)
    sp = lk.value_spoilers(ALL_CUES, tl)
    A(f"答えの数字が声より先に出る: {len(sp)} 件 {[s_[0] for s_ in sp[:3]]}", not sp)
    if frames is not None:
        allt = [(f[0], e) for f in frames for e in f[1]]
        # 文字の箱の交わり
        pairs = lk.text_box_overlaps(frames, skip=[(T_ES, T_ES + 0.6)])
        spans = lk.collapse_overlaps(pairs)
        lk.write_overlap_report(OUT / "overlap_report.md", frames, pairs, notes=["数えなかったもの: 終了画面への切りかえ（T_ES〜+0.6秒）だけ（章カードも数えた）",
                                                                                  "字幕の行（「字幕: …」）の箱を含めて調べた"])
        for a_, b_, x, y in spans[:8]:
            print(f"  文字の交わり {_ts(a_)}〜{_ts(b_)} 「{x}」と「{y}」")
        A(f"文字の箱の交わり（字幕・付せん・札・棒の枠・図の文字・全コマ）: {len(spans)} 組・{len(pairs)} コマ（期待 0）", not spans)
        small = lk.min_text_size(frames, 40, exempt=lambda s_: s_.startswith("字幕: "))
        for t_, lab, sz in small[:6]:
            print(f"  40px未満 {_ts(t_)} 「{lab}」 {sz:.0f}px")
        A(f"文字の大きさ: 40px 未満 {len(small)} 種（スマホで読める。幅480pxに縮めても約10px）", not small)
        edge = lk.outside_area(frames, skip=[(T_ES, T_ES + 0.6)])
        for t_, lab, bx in edge[:6]:
            print(f"  画面の端 {_ts(t_)} 「{lab}」 {bx}")
        A(f"画面の端（x 48〜1872・y 36〜1044）に近い文字: {len(edge)} 件", not edge)
        ec_fr = [f for f in frames if T_EC0 + 0.5 <= f[0] <= T_EC1 - 0.25]
        ec_lab = {e[0] for f in ec_fr for e in f[1] if not e[0].startswith("字幕: ")}
        A(f"区切り: 前の章の絵は片づいて、画面の文字は Eyecatch.texts() の {len(EC.texts())} 種だけ（{sorted(ec_lab)}）", bool(ec_fr) and ec_lab == EC.texts())
        ec_all = all(EC.texts() <= {e[0] for e in f[1]} for f in frames if T_EC0 + 0.75 <= f[0] <= T_EC1 - 0.25)
        A("区切り: 「ここまで」「ここから」と左右の2行ずつが、区切りの間ずっと出ている", ec_all)
        tp = teaser.check([f for f in frames if f[0] <= 5.0 + 1e-9])
        A(f"OpeningTeaser.check（0秒目に問いの全行・伏せ忘れなし）: {tp or 'OK'}", not tp)
        q0 = [e for f in frames if f[0] == 0.0 for e in f[1] if e[0] in QLINES]
        A(f"冒頭の問い: 0秒目に4行そろって {min(e[5] for e in q0):.0f}px（90px 以上）・サムネと同じ言葉「{QTXT}」", len(q0) == 4 and min(e[5] for e in q0) >= 90 and QTXT == "2200年前の人は、棒1本で地球の大きさを当てた？")
        digs = sorted({e[0] for t_, e in allt if HIDE_AT + 0.1 <= t_ <= T_OPEN - 0.1 and e[1] > 1030 and 560 <= e[2] <= 704 and _re.search(r"\d", e[0])})
        A(f"答えの箱: 3.2秒〜「約4万km」に開くまで、数字を伏せている（箱の中の数字 {digs}）", not digs)
        opened = first_seen(frames, lambda s_, e: s_ == "約4万km" and e[1] > 1030 and 560 <= e[2] <= 704)
        A(f"答えの箱は「800kmの50倍で、4万km」の声（{Sk('c0_x50', 0.45):.1f}秒ごろ）のころに開く（{opened}秒に初めて出る）", opened is not None and opened >= Sk("c0_x50", 0.0) - 0.3 and opened <= E(ID["c0_x50"]))
        # 答えの数字（文字）が声より先に出ていないか
        tokens = [("48%", "c1_hit", True), ("66%", "c1_hit2", True), ("99.7%", "c2_99", True), ("84", "c2_84", True), ("86%", "c3_86", True), ("95%", "c3_95", True),
                  ("約10%", "c2_res", True), ("約2%", "c2_mid", True), ("1.8%", "c3_mad", True), (f"{ihalf(CONST['no_err']):,}km", "c4_632", True),
                  (f"{ihalf(CONST['correct']):,}km", "c4_cor", True), ("＋1.6%", "c4_16", True), ("844km", "c4_844", True), ("790km", "c4_790", True),
                  ("0.4度", "c4_sun", True), ("96%", "c5_96", True), ("約3.9万km", "c6_157", True), ("約4.6万km", "c6_185", True), ("約800km", "c0_800", True),
                  ("中央値 4万600km", "c1_med", True), ("約3万9千km", "c6_157", False), ("約4万6千km", "c6_185", False), ("7.2度", "c0_72", False), ("360 ÷ 7.2 ＝ 50", "c0_50", True)]
        for tok, key, exact in tokens:
            if key == "c6_157" and "3万9" in tok:
                continue
            ft = first_seen(frames, (lambda s_, e, tok=tok: s_ == tok) if exact else (lambda s_, e, tok=tok: tok in s_))
            if tok in ("約3万9千km", "約4万6千km"):
                key_ = "c6_157" if "3万9" in tok else "c6_185"
                ft = first_seen(frames, lambda s_, e, tok=tok: tok in s_.replace(" ", "").replace("×157.5m＝", "").replace("×185m＝", ""))
                key = key_
            lim = S(ID[key]) - 0.3
            A(f"画面の「{tok}」は声の文（{key}）の頭 {S(ID[key]):.1f}秒の 0.3秒前より早く出ない（初出 {ft if ft is None else round(ft, 2)}秒）", ft is not None and ft >= lim)
        # 画面の数字は data.json の値（か閉じた目もりなど）
        ok_ = _allowed_nums()
        extra = {}
        for t_, e in allt:
            lab = e[0]
            if lab.startswith("字幕: ") or lab in CARD_LINES:
                continue
            if _re.match(r"^\d[\d,]*回$", lab):
                continue                                                 # 早回しの「N回」
            if _re.match(r"^\d[\d,]*km$", lab) and t_ < HIDE_AT + 0.05:
                continue                                                 # 冒頭の数字の上がり
            for m in _re.finditer(NUM_RE, lab):
                v = float(m.group(0).replace(",", ""))
                if v not in ok_:
                    extra.setdefault(m.group(0), (lab, t_))
        for v, (s_, t_) in list(extra.items())[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」 {_ts(t_)}")
        A(f"画面に出る数字は、すべて data.json の値（の四捨五入）か、目もりなどの閉じた値: 余分 {len(extra)}個", not extra)
        both = [t_ for t_, e in allt if e[0] == "5%以内" and t_ < S("ch7") and any(e2[0] == "10%以内" for t2, e2 in allt if abs(t2 - t_) < 1e-9 and t2 < S("ch7"))]
        A(f"基準の札: 「10%以内」と「5%以内」が同じコマに並ばない（切り替えで入れかわる）: {len(both)}コマ", not both)
        A("1章: 付せん「当たり ＝」「本当の値から10%以内」「読み取り 1.5cm」「ぶれの大きさはこの動画の条件」「距離のぶれ 10%」・図の名札（棒 1m・影の先は ぼやける）",
          all(first_seen([f for f in frames if S("ch1") <= f[0] < S("ch2")], lambda s_, e, k=k: s_ == k) is not None for k in ["当たり ＝", "本当の値から10%以内", "読み取り 1.5cm", "ぶれの大きさはこの動画の条件", "距離のぶれ 10%", "棒 1m", "影の先は ぼやける", "棒1m・目で読む"]))
        A("2章: 付せん「距離のぶれ」「たとえば、きちんと測れたら」「地球一周 ＝」「ずれ」「ずれの中央値」・ぶれの内訳の名札（距離・影の先の癖・影の読み取り）・棒の細い印 84",
          all(first_seen([f for f in frames if S("ch2") <= f[0] < S("ch3")], lambda s_, e, k=k: s_ == k) is not None for k in ["10% → 2%", "たとえば、きちんと測れたら", "地球一周 ＝", "ずれ", "ずれの中央値", "距離", "影の先の癖", "影の読み取り", "84"]))
        A("4章: 棒の名札「エラトステネスの考え方」「正しい計算」・付せん「＋1.6%」・図の「844km」「790km」「0.4度」「緯度の差」",
          all(first_seen([f for f in frames if S("ch4") <= f[0] < S("ch5")], lambda s_, e, k=k: k in s_) is not None for k in ["エラトステネスの考え方", "正しい計算", "＋1.6%", "844km", "790km", "0.4度", "緯度の差"]))
        A("5章: 「測れない ×」（答えが負の回は ×。負の値は出さない）・棒「棒1m・目で読む」8・「800kmの町」48・「影の先をくっきり」96",
          all(first_seen([f for f in frames if S("ch5") <= f[0] < S("ch6")], lambda s_, e, k=k: k in s_) is not None for k in ["測れない ×", "棒1m・目で読む", "800kmの町", "影の先をくっきり", "8.5%", "48%", "96%", "7.2度", "0.9度", "読み取りのぶれ 約0.5度", "差が ぶれに埋もれる", "※ 角度は大きく描いてあります"]))
        neg_txt = [e[0] for t_, e in allt if _re.search(r"-\d|−\d", e[0])]
        A(f"画面に負の数は出ない: {neg_txt[:3]}", not neg_txt)
        A("6章: 付せん「250,000スタディオン」「252,000」「1スタディオン ＝ ？m」・「決着していない」・棒「157.5mなら」約3.9万km・「185mなら」約4.6万km・「本当の値」",
          all(first_seen([f for f in frames if S("ch6") <= f[0] < S("ch7")], lambda s_, e, k=k: k in s_) is not None for k in ["250,000スタディオン", "252,000", "1スタディオン ＝ ？m", "決着していない", "157.5mなら", "約3.9万km", "185mなら", "約4.6万km", "本当の値"]))
        f7 = min(frames, key=lambda f: abs(f[0] - (T_ES - 0.3)))
        n7 = {e[0] for e in f7[1]}
        A("まとめ: 梯子の棒5本（名札5つ・48 → 66 → 99.7 → 86 → 95・10%以内/ここから5%以内）・左ページに「大事なのは」", {"棒1m・目で読む", "＋棒を10mに", "＋距離をきちんと", "＋10日の平均", "＋影の先をくっきり", "48%", "66%", "99.7%", "86%", "95%", "10%以内", "ここから 5%以内"} <= n7)
        tes = T_ES + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1] if not e[0].startswith("字幕: ") and (e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936)]
        for t_, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t_)} 「{s_}」")
        A(f"終了画面の文字はページの中・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件", not out_es)
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        A(f"終了画面の文字は すべて 38px 以上: {es_small}", not es_small)
        ans = [r[1] for r in end_rows()]
        es_ans = {e[0]: e[5] for f in frames if f[0] >= T_ES + 1.0 for e in f[1] if e[0] in ans}
        A(f"終了画面の答えの付せん（左ページ）の答えの文字は 60px 以上: {es_ans}", len(es_ans) == 3 and min(es_ans.values()) >= 59.5)
        es_last = [e for f in frames if f[0] >= Sk("c7_ch", 0.0) + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        A("終了画面の付せん「チャンネル登録」の3行が出る・52px 以上", len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5)
        A(f"終了画面: 最後の約15秒（{DUR - T_ES:.1f}秒）・定型2行は最後の文だけ（「このチャンネルでは」{Sk('c7_ch'):.1f}秒〜）", 10.0 <= DUR - T_ES <= 20.0 and Sk("c7_ch") > T_ES)
        A("まとめの締め: 結果 → 持ち帰る一言 → 問い（3文）→ 注意書き1文 → 定型2行の順", S(ID["c7_2"]) < S(ID["c7_3"]) < S(ID["c7_4"]) < S(ID["c7_5"]) < S(ID["c7_ch"]) < S(ID["c7_sub"]))
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
            frames = lk.scan_frames(draw, DUR, timeline=tl)
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
    frames = lk.scan_frames(draw, DUR, timeline=tl)
    scene_checks(frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
