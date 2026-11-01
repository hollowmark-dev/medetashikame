"""電車の窓が曇るのは、外が寒いから？ 人が多いから？ 空いた寒い朝の車両と、混んだ少し暖かい朝の車両を1万回。— 2026-10-26 作成（公開予定 11/1・45秒前後）

くらべるのは「窓ガラスの内側が曇るか」だけ。

モデル（車両1両。窓は単板ガラスとして計算＝電車の窓が単板か複層かは確認できなかった）
  窓ガラス内側の温度 θ = 車内温度 − (車内温度 − 外の温度) × U ÷ α_in
      U（単板ガラスの熱貫流率）= 5.8 W/(m²K)（透明単板。板硝子協会の表を引く 中小機構 https://j-net21.smrj.go.jp/development/energyeff/Q1225.html ）
      α_in（室内側の表面熱伝達率）= 8.1〜9.3 W/(m²K)（中央 8.7。北海道立総合研究機構 https://www.hro.or.jp/upload/50471/1041204.pdf 。窓の表面温度の式もここ）
      走行風を受ける外側は U が 6〜7 とやや大きい側（物理的な推測・出典なし）だが、5.8 で固定した。曇る側に倒れる向きなので、結論は弱めに出る
  車内の水蒸気（定常）:
      入ってくる水蒸気 = 換気で入る外の空気の水蒸気 ＋ 乗客の息と汗 ＝ 出ていく量
      乗客 N 人 = 乗車率 × 定員。定員 140〜160 人/両（E233系の例 https://en.wikipedia.org/wiki/E233_series 。FACTCHECK では 142〜160）
      乗車率の幅 20%〜200%（一様。乗車率の意味と 100/150/200% の目安 https://trafficnews.jp/post/37079 。幅は仮定）
      1人あたりの水蒸気 g = 30〜80 g/h（静座 24℃で約49 g/h、20℃で約31、26℃で約59 … https://www.engineeringtoolbox.com/metabolic-heat-persons-d_706.html の潜熱から換算。
          住宅の省エネ計算 https://hc-energy.readthedocs.io/ja/latest/_sources/contents/03_30_eval_occupants.rst.txt では 59〜107 g/h。電車は立ち客が多い。
          日本の空調設計資料の表そのものは確認できず、30〜80 g/h を幅とした＝FACTCHECK の判断）
      換気量 Q = 0.30〜0.80 m³/s（空調の強制換気 0.43 m³/s、窓開けのみ 0.3〜0.4 m³/s、併用 約0.8 m³/s。鉄道総研のシミュレーション結果で実車計測ではない
          https://www.mlit.go.jp/tetudo/content/001375661.pdf 、解説 https://tetsudo-ch.com/10854939.html 。
          乗車率が変わっても換気量は変わらない、という結果なので、乗客数と独立に引いた。冬は窓を閉めるので主は空調の外気導入）
      車内の空気の体積 V = 115〜135 m³（確認できない。長さ20m×幅2.95m×高さ3.62m の外寸（E233系）から車内高約2.2〜2.3mとして見積り。
          MLIT 資料の「約5分に1回入れ替わり・0.43 m³/s」から逆算した約129 m³ とも矛盾しない）
      水蒸気の分圧 e_ss = e_外 + 乗客の水蒸気 ÷ 換気量 ×（車内の絶対温度 ÷ 216.7）   [hPa]。
          外の空気は 気温・湿度から e_外 = 湿度 × e_s(外気温)。部屋に入っても水蒸気の分圧は変わらない（温めても混合比は同じ）として扱う。
      e_s(T) = 6.112 × exp(17.62 T/(243.12+T)) [hPa]（Magnus の式・WMO）。露点 Td は 逆に解く。
      乗車前の車内は外の空気と同じ水蒸気（仮定。車庫で換気されてきた）。乗客が乗ると、時定数 V/Q（約2〜7分）で定常に近づく。
  曇り: θ < Td（窓ガラス内側の温度が、車内の空気の露点より低い）
  幅（1回ごとにすべてでたらめ・一様）:
      外の気温 −3〜12℃（朝の都市部の冬〜春先を見込んだ幅・仮定）、外の湿度 40〜70%（気象庁 東京の平年値 1月 51%・2月 52% を見込んだ・仮定）
          https://www.data.jma.go.jp/stats/etrn/view/nml_sfc_ym.php?prec_no=44&block_no=47662
      車内の温度 18〜24℃（暖房の設定の幅。19〜23℃は私鉄3社の例＝FACTCHECK。18〜24℃は仮定）
  ドアの開閉（ひねり。仮定）:
      駅でドアが開いている間 20〜40 秒、換気量が ＋2〜6 m³/s になる（外の空気が入る量。実測の値は確認できなかった＝仮定）。
      その間の車内の水蒸気を時定数で計算し、ドアが閉まる直前に 窓ガラス内側の温度が露点を上回れば「曇りが引いた」。
      車内の温度とガラスの温度は変わらないとした（冷たい空気が入ると実際はガラスも冷える＝曇りが引く側には弱めに出る）。

問い: 「電車の窓が曇るのは、／外が寒いから？／人が多いから？」
      選択肢: 外が寒いから ／ ほぼ同じ ／ 人が多いから（記号の並びは LABELS の順。正解の記号は B）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回を 外の気温（寒い1/3・暖かい1/3）と 乗車率（少ない1/3・多い1/3）で分け、
      a =「寒い × 空いている」で曇った割合、b =「暖かい × 混んでいる」で曇った割合。
      b − a ≥ 20ポイント → 人が多いから、a − b ≥ 20ポイント → 外が寒いから、それ以外 → ほぼ同じ。
画面に出す「片方だけ変えた」比較（同じ1万回から）:
      ① 外の気温は寒い1/3のまま、人だけ 少ない → 多い にしたとき 曇る割合が何ポイント上がるか
      ② 乗車率は少ない1/3のまま、外だけ 暖かい → 寒い にしたとき 何ポイント上がるか
ひねり: 「では、ドアが開いたら？」→ 曇っていた窓のうち ドアが開いている間に引く割合。
締め: 「あなたの朝の電車、窓は曇っていますか？」（答えは出さない）＋「コメントで教えてください」

乱数の種は見本（2両の見た目）のために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "densha-kumori"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261101
U_GLASS = 5.8                                       # W/(m²K) 単板
ALPHA_IN = (8.1, 9.3)                               # W/(m²K)
T_OUT, T_IN, RH_OUT = (-3.0, 12.0), (18.0, 24.0), (0.40, 0.70)
OCC, CAP = (0.20, 2.00), (140.0, 160.0)             # 乗車率、定員（人）
G_PERSON = (30.0, 80.0)                             # g/h/人
VOL, Q_VENT = (115.0, 135.0), (0.30, 0.80)          # m³、m³/s
Q_DOOR, DOOR_SEC = (2.0, 6.0), (20.0, 40.0)           # ドアが開いている間の ＋換気量 m³/s、秒

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_GAP = 0.20                                     # 20ポイント


def answer_by_rule(a, b):
    """a = 寒い×空いている の曇った割合、b = 暖かい×混んでいる の曇った割合。'crowd' / 'same' / 'cold'"""
    if b - a >= RULE_GAP:
        return "crowd"
    if a - b >= RULE_GAP:
        return "cold"
    return "same"


def es_hpa(T):
    return 6.112 * np.exp(17.62 * np.asarray(T, float) / (243.12 + np.asarray(T, float)))


def dewpoint(e):
    """水蒸気の分圧 e[hPa] から露点[℃]（Magnus の逆）"""
    l = np.log(np.asarray(e, float) / 6.112)
    return 243.12 * l / (17.62 - l)


def draw_params(rng, n):
    u = lambda lh: rng.uniform(lh[0], lh[1], n)    # noqa: E731
    return dict(Tout=u(T_OUT), Tin=u(T_IN), alpha=u(ALPHA_IN), rh=u(RH_OUT), occ=u(OCC), cap=u(CAP), g=u(G_PERSON),
                V=u(VOL), Q=u(Q_VENT), Qd=u(Q_DOOR), Td=u(DOOR_SEC))


def physics(d):
    """曇りの判定に使う量。戻り値は dict（配列）"""
    npax = d["occ"] * d["cap"]
    e_out = d["rh"] * es_hpa(d["Tout"])
    gen = npax * d["g"] / 3600.0                                    # 乗客が出す水蒸気 g/s
    # 密度[g/m³]の増え = gen / Q。分圧[hPa]へ: × (T+273.15)/216.7
    de = gen / d["Q"] * (d["Tin"] + 273.15) / 216.7
    e_ss = e_out + de
    theta = d["Tin"] - (d["Tin"] - d["Tout"]) * U_GLASS / d["alpha"]
    td_ss = dewpoint(e_ss)
    return dict(npax=npax, e_out=e_out, de=de, e_ss=e_ss, theta=theta, td=td_ss, fog=theta < td_ss,
                margin=td_ss - theta, rh_in=e_ss / es_hpa(d["Tin"]))


def door(d, ph):
    """ドアが開いている間の水蒸気。戻り値: ドアが閉まる直前の分圧 e_end[hPa]"""
    qt = d["Q"] + d["Qd"]
    de_d = ph["de"] * d["Q"] / qt                                   # 換気が増えた間の定常の増え分
    e_tgt = ph["e_out"] + de_d
    k = np.exp(-qt * d["Td"] / d["V"])
    return e_tgt + (ph["e_ss"] - e_tgt) * k


def e_at(d, ph, t_s):
    """乗車後 t_s 秒の水蒸気の分圧（外と同じ空気から、時定数 V/Q で定常へ）。配列でも1回ぶんでも可"""
    return ph["e_ss"] + (ph["e_out"] - ph["e_ss"]) * np.exp(-d["Q"] * t_s / d["V"])
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
    ph = physics(d)
    e_end = door(d, ph)
    r = dict(p=d, ph=ph, e_end=e_end, td_end=dewpoint(e_end))
    r["fog_end"] = ph["theta"] < r["td_end"]
    _RES["m"] = r
    return r


def tertiles(r):
    p = r["p"]
    t_lo, t_hi = np.quantile(p["Tout"], [1 / 3, 2 / 3])
    o_lo, o_hi = np.quantile(p["occ"], [1 / 3, 2 / 3])
    return dict(cold=p["Tout"] <= t_lo, warm=p["Tout"] >= t_hi, low=p["occ"] <= o_lo, high=p["occ"] >= o_hi,
                t_lo=float(t_lo), t_hi=float(t_hi), o_lo=float(o_lo), o_hi=float(o_hi))


def shown():
    r = results()
    ph = r["ph"]
    fog = ph["fog"]
    tt = tertiles(r)
    P = lambda m: float(fog[m].mean())   # noqa: E731
    a = P(tt["cold"] & tt["low"])
    b = P(tt["warm"] & tt["high"])
    c_ch = P(tt["cold"] & tt["high"])    # 寒い × 混んでいる
    w_lo = P(tt["warm"] & tt["low"])     # 暖かい × 空いている
    n_cell = int((tt["cold"] & tt["low"]).sum())
    fg = fog
    cleared = fg & ~r["fog_end"]
    return dict(a=a, b=b, c_ch=c_ch, w_lo=w_lo, n_cell=n_cell, n_b=int((tt["warm"] & tt["high"]).sum()),
                up_people=c_ch - a, up_cold=a - w_lo,        # ①②
                p_all=float(fog.mean()), tt=tt,
                n_fog_a=int((fog & tt["cold"] & tt["low"]).sum()), n_fog_b=int((fog & tt["warm"] & tt["high"]).sum()),
                door_all=float(cleared.sum() / max(1, fg.sum())),
                door_a=float((cleared & tt["cold"] & tt["low"]).sum() / max(1, (fg & tt["cold"] & tt["low"]).sum())),
                door_b=float((cleared & tt["warm"] & tt["high"]).sum() / max(1, (fg & tt["warm"] & tt["high"]).sum())),
                rh_med=float(np.median(ph["rh_in"])), npax_med=float(np.median(ph["npax"])),
                tau_q=np.percentile(r["p"]["V"] / r["p"]["Q"] / 60.0, [10, 50, 90]),
                dew_med=float(np.median(ph["td"])), theta_med=float(np.median(ph["theta"])),
                de_med=float(np.median(ph["de"])))


def report():
    sh = shown()
    tt = sh["tt"]
    print(f"曇った割合 全体 {sh['p_all']:.3f}   a(寒い×空いている)={sh['a']:.4f}  b(暖かい×混んでいる)={sh['b']:.4f}  "
          f"b−a={100 * (sh['b'] - sh['a']):+.1f}pt  答え {answer_by_rule(sh['a'], sh['b'])}")
    print(f"  セル {sh['n_cell']}回（寒い≦{tt['t_lo']:.2f}℃ / 暖かい≧{tt['t_hi']:.2f}℃、空き≦{tt['o_lo'] * 100:.0f}% / 混み≧{tt['o_hi'] * 100:.0f}%）"
          f"  曇った回数 a:{sh['n_fog_a']} b:{sh['n_fog_b']}")
    print(f"  寒い×混んでいる {sh['c_ch']:.4f}   暖かい×空いている {sh['w_lo']:.4f}")
    print(f"  ① 寒い1/3のまま 人だけ 少→多: {100 * sh['up_people']:+.1f} ポイント    ② 空いている1/3のまま 外だけ 暖→寒: {100 * sh['up_cold']:+.1f} ポイント"
          f"  → 効いたのは {'人' if sh['up_people'] > sh['up_cold'] else '外の寒さ'}")
    print(f"  ドア: 曇っていた窓のうち引いた割合 全体 {sh['door_all']:.3f}  a のセル {sh['door_a']:.3f}  b のセル {sh['door_b']:.3f}")
    print(f"  車内の湿度の中央値 {sh['rh_med'] * 100:.0f}%  乗客数の中央値 {sh['npax_med']:.0f}人  時定数 V/Q 10/50/90% {np.round(sh['tau_q'], 1)} 分"
          f"  露点の中央値 {sh['dew_med']:.1f}℃ 窓の温度の中央値 {sh['theta_med']:.1f}℃")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    sys.exit(0)


# =====================================================================
# 見本（寒い×空いている の1両 と 暖かい×混んでいる の1両）を選ぶ
# =====================================================================
TAU_END = 14.0                                      # 見本の早送りが終わる「乗車から」の分
_SAMPLE = None


def _e_t(S, tau_min):
    """見本の 乗車から tau_min 分の 水蒸気の分圧[hPa]（外と同じ空気から、時定数 V/Q で定常へ）"""
    q = S["q"]
    return S["e_ss"] + (S["e_out"] - S["e_ss"]) * math.exp(-q["Q"] * tau_min * 60.0 / q["V"])


def _td_t(S, tau_min):
    return float(dewpoint(_e_t(S, tau_min)))


def _rh_t(S, tau_min):
    return _e_t(S, tau_min) / float(es_hpa(S["q"]["Tin"]))


def _pick(cell_a, cell_b, want_fog):
    r = results()
    p, ph = r["p"], r["ph"]
    tt = tertiles(r)
    m = tt[cell_a] & tt[cell_b]
    idx = np.nonzero(m)[0]
    tau_q = p["V"] / p["Q"] / 60.0                       # 時定数（分）
    e_end = ph["e_ss"] + (ph["e_out"] - ph["e_ss"]) * np.exp(-p["Q"] * TAU_END * 60.0 / p["V"])
    mg_end = dewpoint(e_end) - ph["theta"]
    ok = (ph["fog"][idx] == want_fog) & (tau_q[idx] <= 5.0)
    ok &= (mg_end[idx] >= 1.0) if want_fog else (mg_end[idx] <= -1.5)
    cand = idx[ok]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    rngs = dict(Tout=15.0, Tin=6.0, occ=1.8, V=20.0, Q=0.5)
    dist = np.zeros(len(cand))
    for k, w in rngs.items():
        dist += np.abs(p[k][cand] - np.median(p[k][idx])) / w
    same = idx[(ph["fog"][idx] == want_fog)]
    dist += np.abs(ph["margin"][cand] - np.median(ph["margin"][same])) / 4.0
    return int(cand[np.argmin(dist)])


def sample():
    """見本: 1万回の中の2回（その回の値そのもの）。それぞれ 条件のセルの真ん中の値に近く、セルの多数派の結果になる回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p, ph = r["p"], r["ph"]
    S = {}
    for key, (ca, cb, wf) in (("cold", ("cold", "low", False)), ("crowd", ("warm", "high", True))):
        i = _pick(ca, cb, wf)
        S[key] = dict(i=i, q={k: float(v[i]) for k, v in p.items()}, theta=float(ph["theta"][i]), e_out=float(ph["e_out"][i]),
                      e_ss=float(ph["e_ss"][i]), fog=bool(ph["fog"][i]), npax=float(ph["npax"][i]), td_ss=float(ph["td"][i]),
                      rh_ss=float(ph["rh_in"][i]))
    _SAMPLE = S
    return S


if __name__ == "__main__" and "--pick" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    for k, S in sample().items():
        q = S["q"]
        print(k, "回", S["i"], "外", round(q["Tout"], 1), "℃ 車内", round(q["Tin"], 1), "乗車率", round(q["occ"] * 100), "% (", round(S["npax"]), "人) 窓",
              round(S["theta"], 1), "℃ 露点(定常)", round(S["td_ss"], 1), "湿度(定常)", round(S["rh_ss"] * 100), "% 時定数",
              round(q["V"] / q["Q"] / 60, 1), "分 曇る", S["fog"])
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
note.DATE = "11.1"                                  # 日付欄（公開予定日）

COL_C, INK_C = "#8fbbe8", "#2f63a8"                 # 外が寒いから（水色）
COL_P, INK_P = "#f4ad6a", "#b8601a"                 # 人が多いから（だいだい）
FOG_COL, CLR_COL = "#7fb0dc", "#ffe3a6"             # マス目: 曇った / 曇らなかった
SKIN = "#f7d9bd"

# 記号の並び・正解は ここ（と comment.txt）だけ。LABELS の順を入れ替えたら TAG・CORRECT も合わせる（run_checks が確かめる）
# 規則の答えが「人が多いから」なので、正解が B の位置に来るよう 外が寒いから／人が多いから／ほぼ同じ の並びにした
LABELS = ["外が寒いから", "人が多いから", "ほぼ同じ"]
TAG = {"cold": "A", "crowd": "B"}
CORRECT = 1                                         # answer_by_rule の結果の位置（B）
KEY_LABEL = {"cold": "外が寒いから", "same": "ほぼ同じ", "crowd": "人が多いから"}
NAME = {"cold": "外が寒いから", "crowd": "人が多いから"}
COLS = {"cold": COL_C, "crowd": COL_P}
INKC = {"cold": INK_C, "crowd": INK_P}
CAR_TITLE = {"cold": "寒い朝・空いている", "crowd": "少し暖かい朝・混んでいる"}

BIG_Q = ["電車の窓が曇るのは、", "外が寒いから？ 人が多いから？"]       # 定位置（上）の2行
BIG_Q3 = ["電車の窓が曇るのは、", "外が寒いから？", "人が多いから？"]    # 1コマ目の3行（同じ大きさ）
DETAIL = "冬〜春先の朝・窓は単板ガラスとして計算"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
RACE_LEN = 10.0                                     # T_GO から 乗車から TAU_END 分になるまで
R0 = 0.06                                           # 冒頭の進み（シミュの分／動画の秒）。答えが見えないよう、ほとんど進めない

# 画面の置き場所（車両のカードは 局所座標 900×420 で描いて、移動・拡大する）
WC, HC = 900.0, 420.0
CAR_CX = 520.0
S0, S1 = 0.86, 1.0
Y_INTRO = {"cold": 830.0, "crowd": 830.0 + HC * S0 + 16.0}
Y_FINAL = {"cold": 588.0, "crowd": 588.0 + HC + 8.0}
FLOOR = 366.0
WIN_X, WIN_Y, WIN_W, WIN_H = (150.0, 402.0, 654.0), 106.0, 226.0, 134.0


def setup():
    global TL, T_FIN2, T_VERD, T_G0, T_G1, T_REV, T_ANS2, T_DOOR, T_DOOR2, T_Q, DURATION
    T_FIN2 = T_GO + RACE_LEN
    T_VERD = T_FIN2 - 0.8

    def build(rx):
        ts = np.arange(0, 60, 1 / 200)
        fade = 1 - 0.6 * np.clip((ts - T_MOVE) / (T_FIN2 - T_MOVE), 0, 1)
        sp = np.where(ts < T_MOVE, R0, R0 + (rx - R0) * np.array([ease((t - T_MOVE) / 1.0) for t in ts]) * fade)
        sp = sp * np.array([1 - ease((t - (T_FIN2 - 1.2)) / 1.2) if t > T_FIN2 - 1.2 else 1.0 for t in ts])
        return ts, np.cumsum(sp) / 200

    lo, hi = 0.1, 60.0
    for _ in range(40):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        if float(np.interp(T_FIN2, ts, tau)) > TAU_END:
            hi = mid
        else:
            lo = mid
    ts, tau = build(hi)
    TL = dict(t=ts, tau=np.minimum(tau, TAU_END))
    T_G0 = T_FIN2 + 2.4
    T_G1 = T_G0 + 3.0
    T_REV = T_G1 + 3.0
    T_ANS2 = T_REV + 2.4
    T_DOOR = T_ANS2 + 5.0
    T_DOOR2 = T_DOOR + 2.4
    T_Q = T_DOOR2 + 4.4
    DURATION = T_Q + 6.0


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def pcs(x):
    return f"{int(math.floor(x * 100 + 0.5))}%"


def ival(x):
    v = int(round(x))
    return f"−{abs(v)}" if v < 0 else f"{v}"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, w, col, outline=3.0):
    """太い線（ふちどり付き）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


COATS = ["#7c8fb5", "#c9786b", "#6d9a86", "#a98fc4", "#d6b25a", "#5f6b80", "#b07d54", "#d98fa0"]
SCARF = ["#e8e0d0", "#b84a4a", "#3f6fa8", "#e4b84a", "#4f8a6a"]
HAIR = ["#2b2b33", "#4a3526", "#1f2430", "#6a4a33", "#3a3a44", "#8a7a66"]
PANTS = "#3b4358"


def person(ctx, x, fy, sc, ci, t, ph, pose="stand", arm_up=False, puff=1.0, bob=0.0):
    """人型。(x, fy) は足もとの中心。sc=1 で身長 約170px。pose は stand / sit"""
    coat, scarf, hair = COATS[ci % len(COATS)], SCARF[ci % len(SCARF)], HAIR[(ci * 3 + 1) % len(HAIR)]
    sc = sc * 1.08
    fy = fy - bob
    ctx.save()
    if pose == "stand":
        hip, sh_y, hd = fy - 62 * sc, fy - 130 * sc, fy - 150 * sc
        for dx in (-10, 10):
            thick(ctx, [(x + dx * sc, hip), (x + dx * 1.3 * sc, fy - 5 * sc)], 16 * sc, PANTS, 2.5)
            ctx.arc(x + dx * 1.45 * sc, fy - 2 * sc, 9 * sc, 0, 2 * math.pi)
            ctx.set_source_rgba(*hexrgb("#2a2f3d"))
            ctx.fill()
    else:
        ys = fy - 48.0
        sh_y, hd = ys - 76 * sc, ys - 96 * sc
        thick(ctx, [(x - 4 * sc, ys - 12 * sc), (x + 42 * sc, ys - 12 * sc)], 18 * sc, PANTS, 2.5)
        thick(ctx, [(x + 42 * sc, ys - 12 * sc), (x + 44 * sc, fy - 6 * sc)], 16 * sc, PANTS, 2.5)
        ctx.arc(x + 52 * sc, fy - 3 * sc, 9 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#2a2f3d"))
        ctx.fill()
    torso = (x - 27 * sc, sh_y, 54 * sc, 78 * sc)
    # うで（奥）
    thick(ctx, [(x - 25 * sc, sh_y + 12 * sc), (x - 31 * sc, sh_y + 62 * sc)], 13 * sc, coat, 2.5)
    ctx.arc(x - 31 * sc, sh_y + 66 * sc, 6 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill()
    core.rrect(ctx, *torso, 14 * sc)
    ctx.set_source_rgba(*hexrgb(coat))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    core.rrect(ctx, x - 22 * sc, sh_y - 7 * sc, 44 * sc, 14 * sc, 7 * sc)       # マフラー
    ctx.set_source_rgba(*hexrgb(scarf))
    ctx.fill_preserve()
    _stroke(ctx, 2.6, INK, 0.85)
    if arm_up and pose == "stand":
        thick(ctx, [(x + 24 * sc, sh_y + 10 * sc), (x + 34 * sc, fy - 178 * sc)], 13 * sc, coat, 2.5)
        ctx.arc(x + 34 * sc, fy - 180 * sc, 7 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, 2.4, INK, 0.9)
    else:
        thick(ctx, [(x + 25 * sc, sh_y + 12 * sc), (x + 31 * sc, sh_y + 62 * sc)], 13 * sc, coat, 2.5)
        ctx.arc(x + 31 * sc, sh_y + 66 * sc, 6 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill()
    # 頭
    ctx.arc(x, hd, 25 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    ctx.arc(x, hd, 26.5 * sc, math.pi * 0.98, math.pi * 2.02)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.9)
    for dx in (-9, 9):
        ctx.arc(x + dx * sc, hd + 3 * sc, 2.8 * sc, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
    ctx.arc(x, hd + 13 * sc, 3.6 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#c0645c"))
    ctx.fill()
    # 息（白いもや。上へ）
    if puff > 0:
        for j in range(2):
            u = (t * 0.55 + ph + j * 0.5) % 1.0
            ctx.arc(x + (20 + 16 * u) * sc, hd + 10 * sc - 34 * u * sc, (5 + 10 * u) * sc, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.78 * (1 - u) * puff)
            ctx.fill_preserve()
            _stroke(ctx, 1.6, PENCIL, 0.45 * (1 - u) * puff)
    ctx.restore()


def scenery(ctx, x, y, w, h, scroll, k):
    """窓の外（流れる町なみ）"""
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    g = cairo.LinearGradient(0, y, 0, y + h)
    if k == "cold":
        g.add_color_stop_rgb(0, *hexrgb("#bccad8")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#e2e9ef")[:3])
        c1, c2 = "#8fa0b3", "#a9b8c8"
    else:
        g.add_color_stop_rgb(0, *hexrgb("#a6d3f0")[:3])
        g.add_color_stop_rgb(1, *hexrgb("#e6f4fb")[:3])
        c1, c2 = "#86a9c8", "#a2bfd8"
    ctx.set_source(g)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    for layer, (blds, per, spd, col) in enumerate((
            (((0, 60, 62), (95, 48, 88), (160, 80, 50), (255, 52, 96), (330, 70, 70)), 410.0, 0.5, c2),
            (((20, 74, 78), (130, 56, 104), (215, 90, 60), (330, 60, 92)), 420.0, 1.0, c1))):
        off = (scroll * spd) % per
        for rep in (-1, 0, 1, 2):
            for bx, bw, bh in blds:
                X = x + bx + rep * per - off
                if X > x + w or X + bw < x:
                    continue
                ctx.rectangle(X, y + h - bh, bw, bh)
                ctx.set_source_rgba(*hexrgb(col))
                ctx.fill()
                if layer == 1:
                    ctx.set_source_rgba(*hexrgb("#eef4f8", 0.8))
                    for wy in range(int(y + h - bh + 10), int(y + h - 8), 22):
                        for wx in range(int(X + 9), int(X + bw - 12), 18):
                            ctx.rectangle(wx, wy, 8, 11)
                            ctx.fill()
    ctx.restore()


_BLOT = {}


def fog_on(ctx, x, y, w, h, level, seed):
    """窓ガラスの内側の曇り。下のすみから、じわっと広がって つながる"""
    if level <= 0:
        return
    if seed not in _BLOT:
        rng = np.random.default_rng(seed)
        _BLOT[seed] = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(0.0, 0.3), rng.uniform(22, 46)) for _ in range(30)]
    ctx.save()
    ctx.rectangle(x, y, w, h)
    ctx.clip()
    a = 0.93 * level ** 1.1
    ctx.set_source_rgba(0.92, 0.95, 0.97, a)
    ctx.rectangle(x, y, w, h)
    ctx.fill()
    for (ux, uy, nz, rmax) in _BLOT[seed]:
        thr = 0.55 * (1 - uy) + nz
        r = rmax * clamp01((level * 1.35 - thr) / 0.5)
        if r <= 0.5:
            continue
        ctx.arc(x + ux * w, y + uy * h, r, 0, 2 * math.pi)
        ctx.set_source_rgba(0.99, 0.99, 1.0, 0.7 * clamp01(level * 2))
        ctx.fill()
    for i in range(36):                                              # 小さな水滴
        ux, uy = ((i * 0.6180339 + seed * 0.13) % 1.0), ((i * 0.7548777 + seed * 0.29) % 1.0)
        if level * 1.1 > 0.25 + 0.7 * ((i * 0.31) % 1.0):
            ctx.arc(x + ux * w, y + uy * h, 2.2 + 2.4 * ((i * 0.37) % 1.0), 0, 2 * math.pi)
            ctx.set_source_rgba(0.62, 0.74, 0.88, 0.75)
            ctx.fill()
    if level > 0.7:                                                  # 水滴のすじ
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        for i in range(3):
            sx = x + w * (0.2 + 0.3 * i) + 6 * math.sin(seed + i)
            ctx.move_to(sx, y + h * 0.35)
            ctx.line_to(sx + 2, y + h * (0.55 + 0.12 * i))
            ctx.set_source_rgba(0.6, 0.72, 0.85, 0.55 * (level - 0.7) / 0.3)
            ctx.set_line_width(3.5)
            ctx.stroke()
    ctx.restore()


def fog_level(k, tau):
    S = sample()[k]
    mg = _td_t(S, tau) - S["theta"]
    return float(ease(clamp01(mg / 2.0))) if mg > 0 else 0.0


# ---------- 絵: 車両のカード ----------

def car_xf(k, m):
    s = S0 + (S1 - S0) * m
    y0 = Y_INTRO[k] + (Y_FINAL[k] - Y_INTRO[k]) * m
    return CAR_CX - WC * s / 2, y0, s


_LAYOUT = {}


def people_layout(k):
    """人の並び: [(x, fy, sc, pose, ci, 乗り込む時刻, arm_up)]。見本の乗車率から"""
    if k in _LAYOUT:
        return _LAYOUT[k]
    S = sample()[k]
    n = max(3, int(round(S["q"]["occ"] * 12)))
    rng = np.random.default_rng(100 + (k == "crowd"))
    n_sit = min(n, max(2, int(round(n * 0.4))), 6)
    seat_idx = np.round(np.linspace(0.6, 4.4, n_sit)).astype(int) if n_sit < 6 else np.arange(6)
    seat_x = np.linspace(215, 815, 6)
    items = []
    for j in range(n_sit):
        items.append([seat_x[seat_idx[j]] + rng.uniform(-8, 8), FLOOR, 0.94, "sit", int(rng.integers(0, 50)), 0.0, False])
    stand = n - n_sit
    rows = 1 if stand <= 5 else (2 if stand <= 10 else 3)
    cnts = [stand // rows + (1 if r < stand % rows else 0) for r in range(rows)]
    for r, c in enumerate(cnts):
        xs = np.linspace(205 + 28 * r, 850 - 28 * ((rows - 1 - r) % 2), c) if c > 1 else np.array([520.0])
        for x in xs:
            items.append([float(x) + rng.uniform(-14, 14), FLOOR - 13 * (rows - 1 - r),
                          (0.94 + 0.07 * r / max(1, rows - 1)) if rows > 1 else 1.0,
                          "stand", int(rng.integers(0, 50)), 0.0, bool(rng.uniform() < 0.45)])
    order = rng.permutation(len(items))
    gap = 0.2 if n <= 8 else 0.065
    for rank, i in enumerate(order):
        items[i][5] = 0.12 + rank * gap
    # 描く順: 座っている人 → 奥の列 → 手前の列
    items.sort(key=lambda it: (it[3] != "sit", it[1]))
    _LAYOUT[k] = items
    return items


def draw_car(ctx, k, t, tau, m):
    S = sample()[k]
    q = S["q"]
    x0, y0, s = car_xf(k, m)
    ga = clamp01((m - 0.85) / 0.15)                                 # 数字の札は、問いが上に移ったあとで出す
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(s, s)
    core.rrect(ctx, 0, 0, WC, HC, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    # --- 題 ---
    xd, yd = 40, 28
    fill(ctx, (1, 1, 1, 0.92))
    ctx.arc(xd, yd, 22, 0, 2 * math.pi)
    ctx.fill()
    note.pen_circle(ctx, xd, yd, 22, 22, INKC[k], seed=13 + (k == "crowd"), width=3.4)
    text(ctx, TAG[k], xd, yd, 30, INKC[k])
    text(ctx, CAR_TITLE[k], 76, yd, 40, INKC[k], align="left")
    text(ctx, f"乗車率 {q['occ'] * 100:.0f}%", 858, yd, 36, INK, align="right")
    # --- 外の温度計 ---
    tc = 70.0
    if ga > 0:
        text(ctx, "外の気温", tc, 82, 28, INK, bold=False, alpha=ga)
    core.rrect(ctx, tc - 13, 100, 26, 168, 13)
    ctx.set_source_rgba(1, 1, 1, 0.95)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    frac = clamp01((q["Tout"] + 6) / 22.0)
    hh = 150 * frac
    ctx.set_source_rgba(*hexrgb(RED, 0.95))
    ctx.rectangle(tc - 6, 262 - hh, 12, hh + 8)
    ctx.fill()
    ctx.arc(tc, 284, 22, 0, 2 * math.pi)
    ctx.fill_preserve()
    _stroke(ctx, 3.2, INK, 0.9)
    if ga > 0:
        text(ctx, f"{ival(q['Tout'])}℃", tc, 334, 44, RED, alpha=ga)
    # --- 車内（断面）---
    bx0, bx1, by0, by1 = 140.0, 886.0, 56.0, 372.0
    ctx.save()
    core.rrect(ctx, bx0, by0, bx1 - bx0, by1 - by0, 10)
    ctx.clip()
    fill(ctx, hexrgb("#f1ebdc"))
    ctx.rectangle(bx0, by0, bx1 - bx0, by1 - by0)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#d6dbe1"))
    ctx.rectangle(bx0, by0, bx1 - bx0, 46)                         # 天井
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#c9b99a"))
    ctx.rectangle(bx0, FLOOR - 2, bx1 - bx0, by1 - FLOOR + 2)       # ゆか
    ctx.fill()
    # 窓
    scroll = t * 150.0
    lev = fog_level(k, tau)
    for wi, wx in enumerate(WIN_X):
        scenery(ctx, wx, WIN_Y, WIN_W, WIN_H, scroll, k)
        fog_on(ctx, wx, WIN_Y, WIN_W, WIN_H, lev, 7 + wi + 3 * (k == "crowd"))
        ctx.rectangle(wx, WIN_Y, WIN_W, WIN_H)
        _stroke(ctx, 4.5, INK, 0.85)
    # つり革
    for i, sx in enumerate(np.linspace(215, 815, 7)):
        sw = 3.0 * math.sin(t * 1.7 + i)
        ctx.move_to(sx, by0 + 44)
        ctx.line_to(sx + sw, 150)
        _stroke(ctx, 2.6, PENCIL, 0.8)
        ctx.arc(sx + sw, 160, 10, 0, 2 * math.pi)
        _stroke(ctx, 4.0, "#7d8795", 0.95)
    # ベンチ
    core.rrect(ctx, 150, 244, 722, 72, 8)                            # 背もたれ
    ctx.set_source_rgba(*hexrgb("#5a7fae"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.8)
    core.rrect(ctx, 146, FLOOR - 50, 730, 24, 8)                     # 座面
    ctx.set_source_rgba(*hexrgb("#4a6d9a"))
    ctx.fill_preserve()
    _stroke(ctx, 3.0, INK, 0.85)
    # 人
    for (px, pfy, psc, pose, ci, tb, up) in people_layout(k):
        u = clamp01((t - tb) / 0.75)
        if u <= 0:
            continue
        xs = bx0 - 40 + (px - (bx0 - 40)) * ease(u)
        moving = 0 < u < 1
        pz = "stand" if moving else pose
        bob = 5 * abs(math.sin(t * 13 + ci)) if moving else 0.0
        person(ctx, xs, pfy, psc, ci, t, (ci % 7) / 7.0, pose=pz, arm_up=(up and not moving), puff=0.0 if moving else 1.0, bob=bob)
    ctx.restore()
    core.rrect(ctx, bx0, by0, bx1 - bx0, by1 - by0, 10)
    _stroke(ctx, 3.2, INK, 0.85)
    # 車内の表示（温度・湿度）と、乗車から何分か
    if ga > 0:
        rh = _rh_t(S, tau)
        core.rrect(ctx, 300, by0 + 5, 430, 38, 8)
        ctx.set_source_rgba(*hexrgb("#1f2a3d", 0.95 * ga))
        ctx.fill()
        text(ctx, f"車内 {q['Tin']:.0f}℃・湿度 {rh * 100:.0f}%", 515, by0 + 25, 28, "#ffffff", alpha=ga)
        text(ctx, f"乗車{int(tau)}分後", 150, by0 + 25, 26, INK, align="left", alpha=ga)
    # --- 下の帯: 窓の温度と露点（見本の1回の値）---
    if ga > 0:
        td = _td_t(S, tau)
        done = t >= T_VERD
        text(ctx, f"窓{ival(S['theta'])}℃　露点{ival(td)}℃", 28, 398, 30, INK, align="left", alpha=ga)
        text(ctx, "たとえば、この1回では", 318, 398, 26, PENCIL, align="left", bold=False, alpha=ga)
        if done:
            u = clamp01((t - T_VERD) / 0.35)
            lab = "曇った！" if S["fog"] else "曇らない"
            colr = RED if S["fog"] else INK_C
            text(ctx, lab, 786, 398, 34, colr, alpha=ga * u)
            note.pen_circle(ctx, 786, 398, core.text_width(lab, 34) / 2 + 16, 26, colr, seed=70 + (k == "crowd"), width=4.5,
                            progress=u)
    ctx.restore()


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    m = INTRO.moved(t)
    ctx.push_group()
    for k in ("cold", "crowd"):
        draw_car(ctx, k, t, tau, m)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 1万回のマス目（2つのセル） ----------
G_COLS, G_ROWS, G_CELL = 38, 30, 11
G_Y0 = 640.0
G_X = {"cold": 96.0, "crowd": 562.0}
_GRID = {}
_CELLS = {}


def cell_flags(k):
    """セルの試行の 曇った(1)/曇らない(0)。試行番号の順"""
    if k in _CELLS:
        return _CELLS[k]
    r = results()
    tt = tertiles(r)
    m = (tt["cold"] & tt["low"]) if k == "cold" else (tt["warm"] & tt["high"])
    _CELLS[k] = r["ph"]["fog"][m].astype(int)
    return _CELLS[k]


def grid_surface(k, n):
    key = (k, int(n) // G_COLS)
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 6:
        _GRID.clear()
    fl = cell_flags(k)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(CLR_COL), bgra(FOG_COL)], np.uint8)
    m = len(fl) if n >= len(fl) else (int(n) // G_COLS) * G_COLS
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[fl[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35)


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    sh = shown()
    prog = clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    titles = {"cold": "寒い × 空いている", "crowd": "暖かい × 混んでいる"}
    for k in ("cold", "crowd"):
        fl = cell_flags(k)
        n = len(fl) * prog
        surf, _ = grid_surface(k, n)
        gx = G_X[k]
        cx = gx + G_COLS * G_CELL / 2
        ctx.set_source_surface(surf, gx, G_Y0)
        ctx.paint_with_alpha(a)
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.rectangle(gx - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
        ctx.stroke()
        text(ctx, titles[k], cx, 610, 34, INKC[k], alpha=a)
        if t >= T_G1 + 0.1:
            u = ease_out((t - T_G1 - 0.1) / 0.3) * a
            p = sh["a"] if k == "cold" else sh["b"]
            text(ctx, f"曇った {pcs(p)}", cx, 1012, 52, RED if k == "crowd" else INK_C, alpha=u)
    # 凡例（色の見本）と 1マス＝1回
    fill(ctx, hexrgb(FOG_COL, a))
    ctx.rectangle(110, 1048, 28, 28)
    ctx.fill()
    fill(ctx, hexrgb(CLR_COL, a))
    ctx.rectangle(290, 1048, 28, 28)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
    ctx.set_line_width(2)
    for xx in (110, 290):
        ctx.rectangle(xx, 1048, 28, 28)
        ctx.stroke()
    text(ctx, "曇った", 148, 1062, 28, INK, align="left", bold=False, alpha=a)
    text(ctx, "曇らなかった", 328, 1062, 28, INK, align="left", bold=False, alpha=a)
    text(ctx, f"1マス＝1回（各 約{fmt(round((len(cell_flags('cold')) + len(cell_flags('crowd'))) / 2 * prog / 100.0) * 100)}回）", 530, 1062, 28, INK, align="left", bold=False, alpha=a)


# ---------- 答え ----------

def answer_key():
    sh = shown()
    return answer_by_rule(sh["a"], sh["b"])


def pt_i(x):
    return int(math.floor(abs(x) * 100 + 0.5))


def reason_text():
    sh = shown()
    k = answer_key()
    l1 = f"寒いままで 人だけ増やすと +{pt_i(sh['up_people'])}ポイント"
    l2 = f"空いたままで 外だけ寒くしても +{pt_i(sh['up_cold'])}ポイント"
    if k == "crowd":
        l3 = "窓を曇らせるのは 人の数"
    elif k == "cold":
        l3 = "窓を曇らせるのは 外の寒さ"
    else:
        l3 = "どちらも 同じくらい効く"
    return f"この置き方なら\n{l1}\n{l2}\n{l3}"


DOOR_Q = "では、ドアが開いて\n外の空気が入ったら？"


def door_a():
    sh = shown()
    return f"この置き方なら 曇った窓の約{pcs(sh['door_all'])}が晴れる"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    note.sticky(ctx, f"正解は {'ABC'[CORRECT]}、{KEY_LABEL[key]}。", 520, 1140, 50, "yellow", fg=RED, a=b, tilt=-0.02)
    r_a = 1 - ease((t - T_DOOR) / 0.3) if t >= T_DOOR else 1.0
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 520, 1322, 32, "blue", a=c, tilt=0.012)
    if t >= T_DOOR:
        d = ease_out((t - T_DOOR - 0.15) / 0.3)
        note.sticky(ctx, DOOR_Q, 520, 1290, 36, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_DOOR2:
        e = ease_out((t - T_DOOR2) / 0.3)
        text(ctx, door_a(), 520, 1420, 32, INK, alpha=e)


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


def big_sizes(max_w):
    s1 = 100.0 * max_w / core.text_width(BIG_Q[0], 100.0)
    s2 = min(100.0 * max_w / core.text_width(BIG_Q[1], 100.0), s1 * 1.6)
    return s1, s2


def big3_size(max_w=860.0):
    """3行とも同じ大きさ。いちばん長い行が max_w になる大きさ"""
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


CD_X, CD_Y = 590.0, 1015.0


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい）・前提・三択（横1列）。その下に2両の電車（0秒目から人が乗り込む）"""
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
            text(ctx, DETAIL, 565, 740, 30, INK, bold=False, alpha=a1)
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
        s1, s2 = big_sizes(850.0)
        sz = min(s1, 47.0)
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
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_grid(ctx, t)
        draw_answer(ctx, t)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fo)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたの朝の電車、\n窓は曇っていますか？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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

def noise_band(dur, k, seed, amp=1.0):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal(int(SR * dur))
    lo = np.convolve(n, np.ones(k) / k, mode="same")
    return lo * amp


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    t_end = T_G0
    rum = noise_band(t_end, 400, 3, 3.0)                  # 電車の走る音（ごおーっ）
    tt = np.arange(len(rum)) / SR
    env_ = (0.7 + 0.3 * np.sin(2 * np.pi * 0.23 * tt)) * np.minimum(1, tt / 0.3) * np.minimum(1, (t_end - tt) / 0.5)
    mx.add(0.0, rum * env_, 0.55)
    k = 0.0
    while k < t_end - 0.5:                                # つなぎ目の音（ガタンゴトン）
        mx.add(k, tick(700, 0.035), 0.22)
        mx.add(k + 0.13, tick(620, 0.03), 0.16)
        k += 0.62 if k < T_GO else 0.45
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_G0 - 1.0, bpm=118, vol=0.30)
    mx.add(T_VERD + 0.2, bell(523.3, 1.2), 0.45)
    mx.add(T_VERD + 0.5, bell(784.0, 1.2), 0.4)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)                   # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_DOOR, blip(1318.5, 0.18), 0.45)              # ドアのチャイム（ピンポン）
    mx.add(T_DOOR + 0.28, blip(987.8, 0.3), 0.45)
    mx.add(T_DOOR2, blip(659.3, 0.14), 0.3)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def _scalar_ref(d, i):
    """1回ぶんを math だけで計算し直す（配列版 physics の答え合わせ）。(窓の温度, 露点, 曇るか)"""
    es = lambda T: 6.112 * math.exp(17.62 * T / (243.12 + T))   # noqa: E731
    n = d["occ"][i] * d["cap"][i]
    e_out = d["rh"][i] * es(d["Tout"][i])
    rho_gen = n * d["g"][i] / 3600.0 / d["Q"][i]                # g/m³
    e_ss = e_out + rho_gen * (d["Tin"][i] + 273.15) / 216.7
    th = d["Tin"][i] - (d["Tin"][i] - d["Tout"][i]) * U_GLASS / d["alpha"][i]
    l = math.log(e_ss / 6.112)
    td = 243.12 * l / (17.62 - l)
    return th, td, th < td


def _euler_density(d, i, t_total, qd=0.0, start="out"):
    """水蒸気の量（g/m³）を 1秒刻みの足し算で。start: 'out'=外と同じ空気から / 'ss'=定常から。戻り値は分圧[hPa]"""
    es = lambda T: 6.112 * math.exp(17.62 * T / (243.12 + T))   # noqa: E731
    Tk = d["Tin"][i] + 273.15
    rho_out = d["rh"][i] * es(d["Tout"][i]) * 216.7 / Tk
    gen = d["occ"][i] * d["cap"][i] * d["g"][i] / 3600.0
    q = d["Q"][i] + qd
    V = d["V"][i]
    rho = rho_out if start == "out" else rho_out + gen / d["Q"][i]
    dt = 0.05
    for _ in range(int(round(t_total / dt))):
        rho += dt * (gen / V - q / V * (rho - rho_out))
    return rho * Tk / 216.7


def run_checks():
    sh = shown()
    r = results()
    p, ph = r["p"], r["ph"]
    checks = []
    # (1) 配列版の物理と、math だけで計算し直した値が合う
    mx_th = mx_td = 0.0
    bad = 0
    for i in range(400):
        th, td, fg = _scalar_ref(p, i)
        mx_th = max(mx_th, abs(th - ph["theta"][i]))
        mx_td = max(mx_td, abs(td - ph["td"][i]))
        bad += int(fg != bool(ph["fog"][i]))
    checks.append(("窓の温度: 配列版 − 計算し直し（最大・℃）", mx_th, 0.0, 1e-9))
    checks.append(("露点: 配列版 − 計算し直し（最大・℃）", mx_td, 0.0, 1e-9))
    checks.append(("曇るかどうかの食い違い（400回中）", float(bad), 0.0, 0.0))
    # (2) 公的資料の例: 室内20℃・外0℃・U=5.8・α=8.7 → 窓の内側 約6.7℃（hro.or.jp の式）。20℃・60% の露点は約12℃
    checks.append(("窓の温度の式（20℃・外0℃・U5.8・α8.7）→ 約6.7℃", 20.0 - 20.0 * U_GLASS / 8.7, 6.7, 0.05))
    checks.append(("露点（20℃・湿度60%）→ 約12℃", float(dewpoint(0.6 * es_hpa(20.0))), 12.0, 0.15))
    # 外気 約8℃以下で単板ガラスが結露する（20℃・60%）
    td20 = float(dewpoint(0.6 * es_hpa(20.0)))
    t_crit = 20.0 - (20.0 - td20) * 8.7 / U_GLASS
    checks.append(("結露する外気温の目安（20℃・60%・単板）→ 約8℃", t_crit, 8.0, 0.3))
    # (3) 水蒸気の足し算（密度の式を1秒刻みで）と、分圧の式が合う（乗車後10分、ドアの間）
    mx_a = mx_b = 0.0
    for i in range(60):
        e_cf = float(ph["e_ss"][i] + (ph["e_out"][i] - ph["e_ss"][i]) * math.exp(-p["Q"][i] * 600.0 / p["V"][i]))
        mx_a = max(mx_a, abs(_euler_density(p, i, 600.0) / e_cf - 1))
        e_d = _euler_density(p, i, p["Td"][i], qd=p["Qd"][i], start="ss")
        mx_b = max(mx_b, abs(e_d / r["e_end"][i] - 1))
    checks.append(("乗車後10分の水蒸気: 足し算 − 式（最大・割合）", mx_a, 0.0, 2e-3))
    checks.append(("ドアが開いている間の水蒸気: 足し算 − 式（最大・割合）", mx_b, 0.0, 2e-3))
    # (4) 水蒸気の収支（定常で 出ていく量 = 乗客が出す量）
    Tk = p["Tin"] + 273.15
    rho_ss = ph["e_ss"] * 216.7 / Tk
    rho_out = ph["e_out"] * 216.7 / Tk
    gen = ph["npax"] * p["g"] / 3600.0
    checks.append(("定常の収支 換気で出る量 − 乗客が出す量（最大・割合）", float(np.max(np.abs(p["Q"] * (rho_ss - rho_out) / gen - 1))), 0.0, 1e-9))
    # (5) ドアが開くと車内の水蒸気は減る（全部の回で）
    checks.append(("ドアが開いた後の水蒸気 ≦ 開く前（全回）", float(np.all(r["e_end"] <= ph["e_ss"] + 1e-12)), 1.0, 0.0))
    # (6) 答え: 決めておいた規則の答えが、画面の答え・記号の並びと同じ
    key = answer_by_rule(sh["a"], sh["b"])
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号は B", float(INTRO.correct), 1.0, 0.0))
    checks.append(("記号 TAG が LABELS の並びと同じ（外が寒いから・人が多いから）",
                   float(LABELS.index(NAME["cold"]) * 10 + LABELS.index(NAME["crowd"])),
                   float("ABC".index(TAG["cold"]) * 10 + "ABC".index(TAG["crowd"])), 0.0))
    # (7) セルは 1万回の約1/9、曇った回数が画面のマス目・割合と同じ
    tt = sh["tt"]
    checks.append(("セル（寒い×空いている）の回数が 約1/9", float(sh["n_cell"]), N_TRIAL / 9.0, 100.0))
    checks.append(("セル（暖かい×混んでいる）の回数が 約1/9", float(sh["n_b"]), N_TRIAL / 9.0, 100.0))
    checks.append(("マス目の曇った割合 a", float(cell_flags("cold").mean()), sh["a"], 1e-12))
    checks.append(("マス目の曇った割合 b", float(cell_flags("crowd").mean()), sh["b"], 1e-12))
    checks.append(("マス目に収まる（回数 ≦ 38×30）", float(max(len(cell_flags("cold")), len(cell_flags("crowd"))) <= G_COLS * G_ROWS), 1.0, 0.0))
    # (8) 片方だけ変えた比較: 向きが妥当（人を増やす・外を寒くする、どちらも曇りやすくなる）
    checks.append(("① 人だけ増やすと 曇る割合は上がる", float(sh["up_people"] > 0), 1.0, 0.0))
    checks.append(("② 外だけ寒くすると 曇る割合は上がる", float(sh["up_cold"] > 0), 1.0, 0.0))
    # (9) 見本は1万回の中の2回で、セルの中にあり、結果がセルの多数派と同じ。早送りの終わりでも結果が同じ
    sm = sample()
    for k, (ca, cb, cell_fog) in (("cold", ("cold", "low", sh["a"] >= 0.5)), ("crowd", ("warm", "high", sh["b"] >= 0.5))):
        S = sm[k]
        i = S["i"]
        checks.append((f"見本({k})がセルの中にある", float(tt[ca][i] and tt[cb][i]), 1.0, 0.0))
        checks.append((f"見本({k})の結果がセルの多数派と同じ", float(S["fog"] == cell_fog), 1.0, 0.0))
        checks.append((f"見本({k})の早送りの終わり({TAU_END:.0f}分)でも結果が同じ",
                       float((_td_t(S, TAU_END) > S["theta"]) == S["fog"]), 1.0, 0.0))
        checks.append((f"見本({k})の定常の露点(式)が1万回の値と同じ", _td_t(S, 1e6), S["td_ss"], 1e-9))
    # (10) 大きく見て: 乗車率が高い三分位ほど曇る
    fog = ph["fog"]
    o = p["occ"]
    q1, q2 = np.quantile(o, [1 / 3, 2 / 3])
    pl, pm, ph_ = fog[o <= q1].mean(), fog[(o > q1) & (o < q2)].mean(), fog[o >= q2].mean()
    checks.append(("乗車率の三分位で 曇る割合が増える", float(pl < pm < ph_), 1.0, 0.0))
    checks.append(("ドアで引く割合は 0〜1", float(0.0 <= sh["door_all"] <= 1.0), 1.0, 0.0))
    check_answers(checks)


def lint():
    """書き出さずに、公開前チェック（文字の位置・大きさ・読み切れる長さ・0.3秒の動き）だけを回す"""
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    n = int(round(DURATION * FPS))
    core._LOG = []
    first = probe = None
    for i in range(n):
        core._CUR_T = i / FPS
        ctx = cairo.Context(surf)
        draw(ctx, i / FPS)
        surf.flush()
        if i == 0:
            first = np.frombuffer(bytes(surf.get_data()), np.uint8)
        elif i == int(0.3 * FPS):
            probe = np.frombuffer(bytes(surf.get_data()), np.uint8)
    log, core._LOG = core._LOG, None
    problems = core.preflight(log, first, probe, DURATION, build_audio())
    if problems:
        print("公開前チェック: 要対応")
        for s in problems:
            print("  -", s)
    else:
        print("公開前チェック: OK")
    return problems


def report_full():
    sh = shown()
    sm = sample()
    print(f"長さ {DURATION:.1f}秒  早送り終わり {T_FIN2:.1f}秒  1万回 {T_G0:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ドア {T_DOOR:.1f}/{T_DOOR2:.1f}  締め {T_Q:.1f}")
    for k, S in sm.items():
        q = S["q"]
        print(f"  見本 {k}: 回{S['i']} 外{q['Tout']:.1f}℃ 車内{q['Tin']:.1f}℃ 乗車率{q['occ'] * 100:.0f}% 窓{S['theta']:.1f}℃ 露点(定常){S['td_ss']:.1f}℃ "
              f"湿度(定常){S['rh_ss'] * 100:.0f}% 時定数{q['V'] / q['Q'] / 60:.1f}分 曇る={S['fog']} 人型{len(people_layout(k))}人")
    print("  理由:", reason_text().replace("\n", " / "), "|", DOOR_Q.replace("\n", ""), "|", door_a())


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--lint" in sys.argv:
        lint()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, 5.8, 7.0, 9.0, 11.0, T_VERD - 0.3, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.8, T_REV + 0.6, T_ANS2 + 0.6, T_DOOR + 0.7, T_DOOR2 + 0.7, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" not in sys.argv:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
