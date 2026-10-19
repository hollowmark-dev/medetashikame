"""レジ、人が少ない列とカゴが軽い列、どっちが早い？ 2人×20点の列と5人×8点の列に、1万回ずつ並ぶ。— 2026-10-13 作成（公開予定 10/19）

モデル（店員さんのレジ2台。2台の店員さんの速さは同じ）
  列A「人が少ない列」: 前に2人、1人20点（合計40点）
  列B「カゴが軽い列」: 前に5人、1人8点（合計40点）
  あなたは、前の客の1人目がレジに着いた瞬間に、列の最後に並ぶ。待ち時間＝自分の番（レジに着く）までの時間。
  1人ぶんの会計 ＝ その他（あいさつ・カゴを置く・ポイントカード・レシートを受け取って離れる） ＋ 品物1点ずつのスキャン ＋ 支払い
    品物1点: 平均3.0秒・標準偏差1.5秒の対数正規分布（Meyer 2009 の店のデータで1点ごとに約2.8〜2.9秒）
    支払い: 方法ごとの実測（関田 2019 の大学生協レジ443件を 小川 2022 が再集計。スキャンが終わって総額を言われてから
            レシートを受け取るまで）。現金 平均15.18秒（標準偏差7.09）／クレジット 12.58秒（件数5件で不確か。標準偏差は6秒と仮定）／
            QR（PayPay） 9.66秒（5.27）／交通系IC・iD 6.7秒（4.5）。いずれも対数正規分布で近似。
            方法の割合は 現金50%・クレジット25%・QR15%・IC10%（仮定。2024年のキャッシュレス比率は金額で42.8%＝経済産業省）
    その他: 平均14秒・標準偏差5秒の対数正規分布（仮定。この部分の実測は見つからなかった）
    店員さんの速さ: 1回ごとに 0.8〜1.25倍（2台とも同じ倍率）。スキャンとその他に掛ける。支払いは客の動作なので掛けない
  1回ぶん: 7人ぶんの会計時間を引き直して、Aの待ち・Bの待ちをくらべる。1万回。

問い: 「レジ、カゴが軽い列と / 人が少ない列、どっちが早い？」（2行。2026-10-14 統括の指示で正解をBに並べ替え）
      A カゴが軽い列 ／ B 人が少ない列 ／ C どっちも同じ
      （画面の札は 列A=カゴが軽い列・列B=人が少ない列。コードの中の "A"/"B" は 人が少ない列/カゴが軽い列 のまま。TAG で読み替える）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「人が少ない列の待ちのほうが短かった回」の割合 p が 60%以上なら B、40%以下なら A、その間なら C。
ひねり: 「人が少ない列の品物が、もっと多かったら？」 列Aの2人に品物を足していき（+0〜+80点）、
      Aが早い回が半々になる点数を1万回ずつで求める → 「1人ぶん ≈ 品物○点」。
締め: 「セルフレジなら、1人は品物何点ぶん？」 自分で通すと1点が約2.2倍遅い（Ciechanowski 2021: 1分に店員16.7点・セルフ7.7点）、
      その他と支払いは1.3倍（仮定。測った値は見つからなかった）として同じように求める。

乱数の種は見本（並んで進む2列）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
照合（check_answers）は run_checks を参照。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "reji-ninzu"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
LANE_N = {"A": 2, "B": 5}                         # 前に並んでいる人数
LANE_ITEMS = {"A": 20, "B": 8}                    # 1人の品物の数（どちらも合計40点）
ITEM_MEAN, ITEM_SD = 3.0, 1.5                     # 1点のスキャン（秒）
OTHER_MEAN, OTHER_SD = 14.0, 5.0                  # あいさつ・カゴ・ポイントカード・レシート・離れる（秒）
PRE_FRAC = 0.6                                    # その他のうち、スキャンの前（あいさつ・カゴを置く）の割合（絵のため）
SPEED = (0.8, 1.25)                               # 店員さんの速さの倍率（1回ごと、2台とも同じ）
PAY = [("現金", 0.50, 15.18, 7.09), ("カード", 0.25, 12.58, 6.0), ("QR", 0.15, 9.66, 5.27), ("IC", 0.10, 6.7, 4.5)]
SELF_ITEM = 16.68 / 7.68                          # セルフレジでは1点が約2.2倍かかる（店員 16.7点/分、セルフ 7.7点/分）
SELF_FIXED = 1.3                                  # セルフレジの その他・支払い の倍率（仮定）
EXTRA = np.arange(0, 82, 2)                       # ひねり: 列Aに足す品物（合計。2人に半分ずつ）

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO = 0.60, 0.40


def answer_by_rule(p_a):
    """p_a = 1万回のうち、Aの待ちのほうが短かった回の割合"""
    if p_a >= RULE_HI:
        return 1                                  # B 人が少ない列
    if p_a <= RULE_LO:
        return 0                                  # A カゴが軽い列
    return 2                                      # C どっちも同じ


def lognorm(rng, mean, sd, size):
    s2 = math.log(1 + (sd / mean) ** 2)
    return rng.lognormal(math.log(mean) - s2 / 2, math.sqrt(s2), size)


def pay_draw(rng, size, scale=1.0):
    """支払いの方法（番号）と時間（秒）"""
    p = np.array([q[1] for q in PAY])
    m = rng.choice(len(PAY), size=size, p=p / p.sum())
    t = np.zeros(size)
    for k, (_, _, mu, sd) in enumerate(PAY):
        sel = m == k
        t[sel] = lognorm(rng, mu, sd, int(sel.sum()))
    return m, t * scale


def lane_draw(rng, n_trial, n_cust, n_items, speed, item_k=1.0, fixed_k=1.0, extra_max=0):
    """1列ぶん（n_trial 回 × n_cust 人）。返り値: 1人ごとの その他・スキャン合計・支払い（秒）と、足す品物の累積"""
    other = lognorm(rng, OTHER_MEAN, OTHER_SD, (n_trial, n_cust)) * fixed_k * speed[:, None]
    items = lognorm(rng, ITEM_MEAN, ITEM_SD, (n_trial, n_cust, n_items)) * item_k * speed[:, None, None]
    method, pay = pay_draw(rng, (n_trial, n_cust), fixed_k)
    out = dict(other=other, scan=items.sum(2), pay=pay, method=method)
    if extra_max:
        ex = lognorm(rng, ITEM_MEAN, ITEM_SD, (n_trial, n_cust, extra_max)) * item_k * speed[:, None, None]
        out["extra_cum"] = np.concatenate([np.zeros((n_trial, n_cust, 1)), np.cumsum(ex, 2)], 2)
    return out


def run(seed, self_check=False):
    """1万回。self_check=True はセルフレジ（店員さんの速さの代わりに、1人ずつの速さ 0.8〜1.25倍）"""
    rng = np.random.default_rng(seed)
    item_k, fixed_k = (SELF_ITEM, SELF_FIXED) if self_check else (1.0, 1.0)
    res = {}
    if self_check:
        sp = {L: rng.uniform(*SPEED, (N_TRIAL, LANE_N[L])) for L in "AB"}
    else:
        s = rng.uniform(*SPEED, N_TRIAL)
    for L in "AB":
        speed = s if not self_check else np.ones(N_TRIAL)
        d = lane_draw(rng, N_TRIAL, LANE_N[L], LANE_ITEMS[L], speed, item_k, fixed_k,
                      extra_max=int(EXTRA[-1]) // 2 if L == "A" else 0)
        if self_check:                            # 1人ずつの速さ（その他とスキャンに）
            for k in ("other", "scan"):
                d[k] = d[k] * sp[L]
            if "extra_cum" in d:
                d["extra_cum"] = d["extra_cum"] * sp[L][:, :, None]
        d["service"] = d["other"] + d["scan"] + d["pay"]
        d["wait"] = d["service"].sum(1)
        res[L] = d
    wA, wB = res["A"]["wait"], res["B"]["wait"]
    pA = np.array([np.mean(wA + res["A"]["extra_cum"][:, :, e // 2].sum(1) < wB) for e in EXTRA])
    res["pA_extra"] = pA
    res["p_a"] = float(np.mean(wA < wB))
    res["break_even"] = break_even(EXTRA, pA)
    return res


def break_even(xs, ps):
    """ps（Aが早い割合）が 0.5 を切る所を、直線でつないで求める"""
    k = int(np.argmax(ps < 0.5))
    if ps[k] >= 0.5:
        return float("nan")
    x0, x1, p0, p1 = xs[k - 1], xs[k], ps[k - 1], ps[k]
    return float(x0 + (p0 - 0.5) / (p0 - p1) * (x1 - x0))


SEED_MAIN, SEED_SELF, SEED_PICK = 20261019, 20261020, 20261021
_RES = {}


def results():
    if not _RES:
        _RES["m"] = run(SEED_MAIN)
        _RES["s"] = run(SEED_SELF, self_check=True)
    return _RES


def mean_fixed(fixed_k=1.0, speed_mean=None):
    """1人ぶんの その他＋支払い の平均（閉じた式）"""
    sm = sum(SPEED) / 2 if speed_mean is None else speed_mean
    p = np.array([q[1] for q in PAY])
    pay = float(np.dot(p / p.sum(), [q[2] for q in PAY]))
    return fixed_k * (OTHER_MEAN * sm + pay)


def shown():
    r = results()
    m, s = r["m"], r["s"]
    wA, wB = m["A"]["wait"], m["B"]["wait"]
    return dict(p_a=m["p_a"], medA=float(np.median(wA)), medB=float(np.median(wB)),
                meanA=float(wA.mean()), meanB=float(wB.mean()), diff_med=float(np.median(wB - wA)),
                n_a=int(np.sum(wA < wB)), n_b=int(np.sum(wB < wA)),
                fixed=mean_fixed(), pA_extra=m["pA_extra"], be=m["break_even"], per=m["break_even"] / 3,
                be_self=s["break_even"], per_self=s["break_even"] / 3, p_a_self=s["p_a"],
                pA_extra_self=s["pA_extra"])


def report():
    sh = shown()
    print(f"Aが早い {sh['p_a']:.4f}（{sh['n_a']}回 / Bが早い {sh['n_b']}回）  答え {'ABC'[answer_by_rule(sh['p_a'])]}")
    print(f"待ち 中央値 A {sh['medA']:.1f}秒 / B {sh['medB']:.1f}秒  平均 A {sh['meanA']:.1f} / B {sh['meanB']:.1f}  差の中央値 {sh['diff_med']:.1f}秒")
    print(f"1人ぶんの その他＋支払い 平均 {sh['fixed']:.1f}秒")
    print("Aに足す点数ごとの Aが早い割合:", {int(e): round(float(p), 3) for e, p in zip(EXTRA, sh["pA_extra"]) if e % 10 == 0})
    print(f"半々になる点数 {sh['be']:.1f}点 → 1人ぶん {sh['per']:.2f}点")
    print(f"セルフ: Aが早い {sh['p_a_self']:.3f}  半々 {sh['be_self']:.1f}点 → 1人ぶん {sh['per_self']:.2f}点")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで進む2列）を選ぶ
# =====================================================================

def sample_lane(rng, n, n_items, speed):
    """見本の1列ぶん。品物1点ずつの時間も残す（絵のため）。分布は lane_draw と同じ"""
    cust = []
    for _ in range(n):
        other = float(lognorm(rng, OTHER_MEAN, OTHER_SD, 1)[0]) * speed
        items = lognorm(rng, ITEM_MEAN, ITEM_SD, n_items) * speed
        m, p = pay_draw(rng, 1)
        cust.append(dict(other=other, items=items, method=int(m[0]), pay=float(p[0]), n=n_items))
    return cust


def schedule(cust):
    """1人ずつの時刻表: 着く S・スキャン開始・1点ずつの終わり・支払い開始 P0・支払い終わり P1・離れる F"""
    t = 0.0
    for c in cust:
        c["S"] = t
        c["scan0"] = t + PRE_FRAC * c["other"]
        c["item_end"] = c["scan0"] + np.cumsum(c["items"])
        c["P0"] = float(c["item_end"][-1])
        c["P1"] = c["P0"] + c["pay"]
        c["F"] = c["P1"] + (1 - PRE_FRAC) * c["other"]
        t = c["F"]
    return t


_SAMPLE = None


def sample():
    """見本: 1万回とは別に引く。条件: 2列の待ちが、それぞれ1万回の真ん中の値に近い（±6秒）。
    カゴが軽い列の支払いに3種類以上が出る。先頭の2人の「あいさつ」の長さがほぼ同じ（冒頭で2列が同じに見えるように）"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    sh = shown()
    for k in range(200000):
        rng = np.random.default_rng(SEED_PICK + k)
        speed = float(rng.uniform(*SPEED))
        if abs(speed - 1.0) > 0.08:
            continue
        lanes = {L: sample_lane(rng, LANE_N[L], LANE_ITEMS[L], speed) for L in "AB"}
        wait = {L: schedule(lanes[L]) for L in "AB"}
        if abs(wait["A"] - sh["medA"]) > 6 or abs(wait["B"] - sh["medB"]) > 6:
            continue
        if len({c["method"] for c in lanes["B"]}) < 3 or 0 not in {c["method"] for c in lanes["B"]}:
            continue
        if abs(lanes["A"][0]["scan0"] - lanes["B"][0]["scan0"]) > 1.0:
            continue
        _SAMPLE = dict(lanes=lanes, wait=wait, speed=speed, seed=SEED_PICK + k)
        return _SAMPLE
    raise SystemExit("見本の候補がない")


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    print("見本 seed", s["seed"], "速さ", round(s["speed"], 3), "待ち", {L: round(v, 1) for L, v in s["wait"].items()})
    for L in "AB":
        for c in s["lanes"][L]:
            print(L, PAY[c["method"]][0], "その他", round(c["other"], 1), "スキャン", round(float(c["items"].sum()), 1),
                  "支払い", round(c["pay"], 1), "着く", round(c["S"], 1))
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
note.DATE = "10.19"                               # 日付欄（公開予定日）

COL_A, INK_A = "#5b8fd6", "#2f63a8"               # 人が少ない列
COL_B, INK_B = "#e8913a", "#b8601a"               # カゴが軽い列
SKIN = "#f6dcc6"
SHIRTS = ["#8fb8de", "#c7a3d6", "#9fcf9b", "#e7a6a1", "#c9b48a", "#a9c4c9", "#d8b4e2", "#b5c99a"]
HAIRS = ["#3a2f2a", "#5a4632", "#2b2b33", "#7a5a3a", "#8c8c8c", "#4a3b2c"]
PANTS = ["#4a5878", "#5d5a52", "#3f4a5c", "#6b5d4f"]
YOU_SHIRT = "#f2c94c"
CLERK = "#6fae86"                                 # 店員さんのエプロン
BASKET = "#e07a7a"
ITEM_COLS = ["#f2c14e", "#e86a5a", "#7cc28a", "#6fa8dc", "#f4a259", "#b39ddb", "#f6e7b0", "#9ad1d4", "#e8b4bc"]

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
T_START = 1.0                                     # 計算の0秒（1人目がレジに着く）。それまでは前の客が離れ、列が1つ進む
INTRO_X = 1.5                                     # 冒頭の速さ（実際の1.5倍）。2列とも1人目のあいさつ〜数点で、差は出ない
RACE_LEN = 9.0                                    # カゴが軽い列の「あなた」がレジに着くまで（動画の秒）
BIG_Q = ["レジ、カゴが軽い列と", "人が少ない列、どっちが早い？"]
DETAIL = "5人×8点 と 2人×20点。どちらも合計40点"
LABELS = ["カゴが軽い列", "人が少ない列", "どっちも同じ"]
CORRECT = 1                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
LANE_NAME = {"A": "人が少ない列", "B": "カゴが軽い列"}
TAG = {"A": "B", "B": "A"}                        # 画面に出す札の字（選択肢の A/B に合わせる）

# 場面の座標: x は画面の px、y は列Aの床が0。列Bの床は LANE_Y["B"]
LANE_Y = {"A": 420.0, "B": 0.0}                   # 札Aのカゴが軽い列を上に
X0, DX = 375.0, 102.0                             # 列の先頭（レジの前）の位置と、1人ぶんの間隔
LAY_INTRO = (1.0, 960.0)                          # (縮める倍率, 列Aの床の y)
LAY_RACE = (0.78, 816.0)
CX_SCENE = 540.0


def setup():
    global TL, RACE_X, T_ENDB, T_RACE_END, T_G0, T_G1, T_BAR, T_REV, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    SB = s["wait"]["B"]
    tau_go = (T_GO - T_START) * INTRO_X
    RACE_X = (SB - tau_go - 0.3 * INTRO_X) / (RACE_LEN - 0.3)
    ts = np.arange(0, 60, 1 / 600)
    tau = np.zeros_like(ts)
    v = 0.0
    for k in range(len(ts)):
        t = ts[k]
        if t < T_GO:
            v = (t - T_START) * INTRO_X
        else:
            sp = INTRO_X + (RACE_X - INTRO_X) * ease((t - T_GO) / 0.6)
            v += sp / 600
        tau[k] = v
    TL = dict(t=ts, tau=tau)
    T_ENDB = float(np.interp(SB, tau, ts))
    T_RACE_END = T_ENDB + 2.0
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.6
    T_BAR = T_G1 + 0.9                            # 棒（待ち時間の真ん中の値）
    T_REV = T_BAR + 1.4                           # 答え
    T_TW = T_REV + 2.8                            # ひねり
    T_TW_RUN = T_TW + 3.5                         # ひねりの札を読み切れる長さ
    T_Q = T_TW_RUN + 5.8                          # 締め
    DURATION = T_Q + 5.4


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of_tau(x):
    return float(np.interp(x, TL["tau"], TL["t"]))


# ---------- 場面の置き場所 ----------

def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def apply_layout(ctx, lay):
    sc, y0 = lay
    ctx.translate(CX_SCENE * (1 - sc), y0)
    ctx.scale(sc, sc)


def to_dev(lay, x, y):
    sc, y0 = lay
    return CX_SCENE + (x - CX_SCENE) * sc, y0 + y * sc


# ---------- 品物とカゴ ----------
_SHAPES = {}


def item_shapes(key, n):
    """カゴの中身（下から順）。形と色は key ごとに決まる。(dx, dy, w, h, 色, 形)"""
    k = (key, n)
    if k in _SHAPES:
        return _SHAPES[k]
    seed = sum((i + 1) * ord(ch) for i, ch in enumerate(repr(key)))
    rng = np.random.default_rng(seed)
    out = []
    per_row = 4
    for i in range(n):
        row, col = divmod(i, per_row)
        kind = int(rng.integers(4))
        w, h = {0: (15, 13), 1: (11, 17), 2: (14, 14), 3: (9, 21)}[kind]
        dx = -21 + col * 14 + rng.uniform(-2, 2) + (7 if row % 2 else 0)
        dx = min(dx, 20)
        dy = -4 - row * 10.5 + rng.uniform(-1.5, 1.5)
        out.append((dx, dy, w, h, ITEM_COLS[int(rng.integers(len(ITEM_COLS)))], kind))
    _SHAPES[k] = out
    return out


def draw_item(ctx, x, y, w, h, col, kind, a=1.0):
    """品物1つ。(x, y) は底のまん中"""
    fill(ctx, hexrgb(col, a))
    if kind == 2:
        ctx.arc(x, y - h / 2, w / 2, 0, 2 * math.pi)
    else:
        core.rrect(ctx, x - w / 2, y - h, w, h, 3 if kind != 3 else 4)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
    ctx.set_line_width(1.6)
    ctx.stroke()
    if kind == 3:                                 # びんの口
        fill(ctx, hexrgb(INK, 0.7 * a))
        ctx.rectangle(x - 2.5, y - h - 4, 5, 4)
        ctx.fill()


def draw_basket(ctx, x, y, items, a=1.0, handle=True):
    """買い物カゴ（横から）。(x, y) は底のまん中。items は item_shapes の一部（下から）"""
    if a <= 0:
        return
    bw_top, bw_bot, bh = 62, 50, 34
    ctx.move_to(x - bw_top / 2, y - bh)
    ctx.line_to(x + bw_top / 2, y - bh)
    ctx.line_to(x + bw_bot / 2, y)
    ctx.line_to(x - bw_bot / 2, y)
    ctx.close_path()
    fill(ctx, hexrgb(BASKET, 0.25 * a))
    ctx.fill()
    for dx, dy, w, h, col, kind in items:
        draw_item(ctx, x + dx, y + dy, w, h, col, kind, a)
    # 前の網（線）
    ctx.set_source_rgba(*hexrgb(BASKET, 0.95 * a))
    ctx.set_line_width(2.2)
    for k in range(1, 5):
        u = k / 5
        xt = x - bw_top / 2 + bw_top * u
        xb = x - bw_bot / 2 + bw_bot * u
        ctx.move_to(xt, y - bh + 6)
        ctx.line_to(xb, y)
    ctx.stroke()
    ctx.move_to(x - bw_top / 2 + 3, y - bh / 2)
    ctx.line_to(x + bw_top / 2 - 3, y - bh / 2)
    ctx.stroke()
    ctx.move_to(x - bw_top / 2, y - bh)
    ctx.line_to(x + bw_top / 2, y - bh)
    ctx.line_to(x + bw_bot / 2, y)
    ctx.line_to(x - bw_bot / 2, y)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(INK, 0.9 * a))
    ctx.set_line_width(2.4)
    ctx.stroke()
    fill(ctx, hexrgb(BASKET, a))
    ctx.rectangle(x - bw_top / 2 - 2, y - bh - 4, bw_top + 4, 6)
    ctx.fill()
    if handle:
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.4)
        ctx.arc(x, y - bh, 22, math.pi * 1.1, math.pi * 1.9)
        ctx.stroke()


# ---------- 人 ----------

def draw_person(ctx, x, f, look, walk=0.0, moving=0.0, basket=None, a=1.0, face=-1, bow=0.0):
    """横から見た人（face=-1 で左向き＝レジのほう）。f は床の y。basket=(品物のリスト) を前に持つ"""
    if a <= 0:
        return
    hs = look["h"]
    ctx.save()
    ctx.translate(x, f)
    ctx.scale(PERSON_K, PERSON_K)
    if face > 0:
        ctx.scale(-1, 1)
    ctx.push_group()
    # 影
    ctx.save()
    ctx.scale(1, 0.25)
    ctx.arc(0, 0, 30, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.15, 0.13, 0.1, 0.12)
    ctx.fill()
    hip = -58 * hs
    # 足（歩くと振る）
    sw = 0.42 * math.sin(walk) * moving
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    for k, ang in enumerate((sw, -sw)):
        fx = math.sin(ang) * (-hip)
        for col, wdt in ((INK, 11), (look["pants"], 7)):
            ctx.set_source_rgba(*hexrgb(col))
            ctx.set_line_width(wdt)
            ctx.move_to(-5 + 10 * k, hip)
            ctx.line_to(-5 + 10 * k + fx, -4)
            ctx.stroke()
    bob = -2.5 * abs(math.sin(walk)) * moving
    ctx.translate(0, bob)
    ctx.rotate(-bow)
    # 体
    core.rrect(ctx, -22, -128 * hs, 44, 76 * hs, 13)
    fill(ctx, look["shirt"])
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(2.6)
    ctx.stroke()
    if look.get("apron"):
        core.rrect(ctx, -20, -112 * hs, 40, 62 * hs, 8)
        fill(ctx, look["apron"])
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(2)
        ctx.stroke()
    # 頭
    hy = -150 * hs
    fill(ctx, SKIN)
    ctx.arc(0, hy, 21, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(2.6)
    ctx.stroke()
    ctx.save()
    ctx.arc(0, hy, 22.5, 0, 2 * math.pi)
    ctx.clip()
    fill(ctx, look["hair"])
    ctx.rectangle(-25, hy - 26, 50, 16)
    ctx.fill()
    ctx.rectangle(6, hy - 26, 20, 38)
    ctx.fill()
    ctx.restore()
    fill(ctx, INK)
    ctx.arc(-11, hy - 1, 2.4, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.set_line_width(1.8)
    ctx.arc(-9, hy + 7, 4.5, math.pi * 0.35, math.pi * 0.8)
    ctx.stroke()
    # 腕とカゴ
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    hx, hyy = (-13, -66 * hs) if basket is not None else (-16, -70 * hs)
    for col, wdt in ((INK, 10), (look["shirt"], 6)):
        ctx.set_source_rgba(*hexrgb(col))
        ctx.set_line_width(wdt)
        ctx.move_to(-7, -116 * hs)
        ctx.line_to(hx, hyy)
        ctx.stroke()
    if basket is not None:
        draw_basket(ctx, hx - 4, hyy + 56, basket, handle=True)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def look_of(L, i):
    """列 L の i 番目の客の見た目（i = n があなた、−1 が前の客）"""
    if i == LANE_N[L]:
        return dict(shirt=YOU_SHIRT, hair="#3a2f2a", pants="#4a5878", h=1.0)
    k = (i + 3) * 7 + (0 if L == "A" else 3)
    return dict(shirt=SHIRTS[k % len(SHIRTS)], hair=HAIRS[(k * 5) % len(HAIRS)], pants=PANTS[k % len(PANTS)],
                h=0.94 + 0.08 * ((k * 37) % 5) / 4)


PERSON_K = 1.22                                   # 人の絵の大きさ
CLERK_LOOK = dict(shirt="#f4f1ea", hair="#2b2b33", pants="#3f4a5c", h=1.0, apron=CLERK)

# ---------- レジ ----------
CTR_X0, CTR_X1, CTR_TOP = 150.0, 322.0, -95.0
SCAN_X = 238.0
IN_X, OUT_X = 292.0, 184.0
CLERK_X = 104.0


def draw_register(ctx, L, flash=0.0):
    f = LANE_Y[L]
    # 案内の柱と札
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(3.5)
    ctx.move_to(140, f + CTR_TOP)
    ctx.line_to(140, f - 236)
    ctx.stroke()
    fill(ctx, "#fffdf6")
    ctx.arc(140, f - 262, 27, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(COL_A if L == "A" else COL_B))
    ctx.set_line_width(4.5)
    ctx.stroke()
    # 台
    core.rrect(ctx, CTR_X0, f + CTR_TOP, CTR_X1 - CTR_X0, -CTR_TOP, 6)
    fill(ctx, "#d9c7a8")
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(2.8)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.35))
    ctx.set_line_width(2)
    ctx.move_to(CTR_X0 + 10, f + CTR_TOP + 22)
    ctx.line_to(CTR_X1 - 10, f + CTR_TOP + 22)
    ctx.stroke()
    # レジの画面
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3)
    ctx.move_to(CTR_X0 + 18, f + CTR_TOP)
    ctx.line_to(CTR_X0 + 18, f + CTR_TOP - 40)
    ctx.stroke()
    core.rrect(ctx, CTR_X0 + 2, f + CTR_TOP - 66, 36, 28, 4)
    fill(ctx, "#4a4f5c")
    ctx.fill()
    fill(ctx, "#bfe3d0")
    ctx.rectangle(CTR_X0 + 7, f + CTR_TOP - 61, 26, 18)
    ctx.fill()
    # スキャナー（読み取ると赤く光る）
    core.rrect(ctx, SCAN_X - 20, f + CTR_TOP - 12, 40, 12, 3)
    fill(ctx, "#3b3f4a")
    ctx.fill()
    if flash > 0:
        ctx.set_source_rgba(*hexrgb("#ff4b4b", 0.55 * flash))
        ctx.move_to(SCAN_X - 16, f + CTR_TOP - 12)
        ctx.line_to(SCAN_X + 16, f + CTR_TOP - 12)
        ctx.line_to(SCAN_X + 4, f + CTR_TOP - 70)
        ctx.line_to(SCAN_X - 4, f + CTR_TOP - 70)
        ctx.close_path()
        ctx.fill()


def lane_text(ctx, L, lay, a=1.0):
    """札の字と列の名前（画面の座標で描く）"""
    f = LANE_Y[L]
    x, y = to_dev(lay, 140, f - 262)
    sc = lay[0]
    text(ctx, TAG[L], x, y, 40 * sc, INK_A if L == "A" else INK_B, alpha=a)
    xl, yl = to_dev(lay, 182, f - 262)
    text(ctx, LANE_NAME[L], xl, yl, 36 * sc, INK_A if L == "A" else INK_B, align="left", alpha=a)


# ---------- 列の状態 ----------

def lane_state(L, tau):
    """τ（計算の秒）での列 L。cur＝いまレジにいる客（−1 は前の客が離れている所、n はあなたの番）、prog＝列が1つ進む途中"""
    s = sample()
    cust = s["lanes"][L]
    n = len(cust)
    you_S = s["wait"][L]
    tau = min(tau, you_S)
    prev = dict(P1=-T_START * INTRO_X, F=0.0)
    cur = -1
    for i, c in enumerate(cust):
        if tau >= c["S"]:
            cur = i
    if tau >= you_S:
        cur = n
    c_now = prev if cur == -1 else (cust[cur] if cur < n else None)
    if c_now is not None and tau >= c_now["P1"]:
        prog = clamp01((tau - c_now["P1"]) / max(1e-6, c_now["F"] - c_now["P1"]))
    else:
        prog = 0.0
    return dict(cur=cur, prog=prog, tau=tau, n=n, cust=cust, c_now=c_now)


def scanned(c, tau):
    """客 c の、τ までに読み終えた点数と、いま流れている品物の進み（0〜1、無ければ None）"""
    if tau < c["scan0"]:
        return 0, None
    k = int(np.searchsorted(c["item_end"], tau, side="right"))
    if k >= c["n"]:
        return c["n"], None
    a = c["scan0"] if k == 0 else c["item_end"][k - 1]
    return k, (tau - a) / (c["item_end"][k] - a)


def ahead_counts(L, tau):
    """あなたの前に残っている人数（支払いが終わっていない人）と品物の点数（まだ読んでいない点数）"""
    st = lane_state(L, tau)
    tau = st["tau"]
    people = items = 0
    for c in st["cust"]:
        if tau >= c["P1"]:
            continue
        people += 1
        k = scanned(c, tau)[0] if tau >= c["S"] else 0
        items += c["n"] - k
    return people, items


def slot_of(st, i):
    """客 i の並んでいる場所（0＝レジの前）"""
    if st["cur"] >= st["n"]:
        return float(i - st["n"])
    return (i - st["cur"]) - st["prog"]


def draw_lane(ctx, L, tau, t):
    st = lane_state(L, tau)
    tau = st["tau"]
    f = LANE_Y[L]
    cust, n, cur = st["cust"], st["n"], st["cur"]
    c = cust[cur] if 0 <= cur < n else None
    flash = 0.0
    bow = 0.0
    if c is not None:
        k, u = scanned(c, tau)
        if u is not None:
            flash = max(0.0, 1 - abs(u - 0.5) * 3)
        if c["S"] <= tau < c["scan0"]:                # あいさつ（店員さんがおじぎ）
            v = (tau - c["S"]) / (c["scan0"] - c["S"])
            bow = 0.22 * math.sin(math.pi * clamp01(v * 1.6))
    draw_person(ctx, CLERK_X, f, CLERK_LOOK, face=1, bow=bow)
    draw_register(ctx, L, flash)
    # 台の上: 右＝客のカゴ（残り）、左＝読み終えた品物
    if c is not None and tau < c["P1"]:
        shapes = item_shapes((L, cur), c["n"])
        k, u = scanned(c, tau)
        left = c["n"] - k - (1 if u is not None else 0)
        if tau < c["P0"]:
            draw_basket(ctx, IN_X, f + CTR_TOP, shapes[:left], handle=False)
        out_shapes = item_shapes((L, cur, "out"), c["n"])
        draw_basket(ctx, OUT_X, f + CTR_TOP, out_shapes[:k], handle=False)
        if u is not None:                             # 流れている1点（客のカゴ → スキャナー → 左のカゴ）
            dx, dy, w, hh, col, kind = shapes[left]
            x = IN_X + (OUT_X - IN_X) * u
            y = f + CTR_TOP - 38 - 34 * math.sin(math.pi * u)
            draw_item(ctx, x, y, w, hh, col, kind)
    # 並んでいる客（後ろから）
    moving = 1.0 if 0 < st["prog"] < 1 else 0.0
    for i in range(n, -1, -1):
        if i <= cur and not (i == n and cur == n):
            continue
        slot = slot_of(st, i)
        x = X0 + slot * DX
        walk = (1 - st["prog"]) * 2 * math.pi * 1.5
        items = item_shapes((L, "you"), 6) if i == n else item_shapes((L, i), cust[i]["n"])
        draw_person(ctx, x, f, look_of(L, i), walk=walk, moving=moving if i != n or cur < n else 0.0,
                    basket=items if not (i == n and cur == n) else None)
    # レジにいる客（カゴは台の上。支払いが終わると、読み終えたカゴを持って離れる）
    if c is not None and tau < c["P1"]:
        draw_person(ctx, X0, f, look_of(L, cur), basket=None)
    if c_left := (st["c_now"] if (st["c_now"] is not None and tau >= st["c_now"]["P1"]) else None):
        u = st["prog"]
        idx = cur
        nitems = 6 if cur == -1 else cust[cur]["n"]
        x = X0 - 30 - 330 * ease(u)
        out = item_shapes((L, idx, "out"), nitems)
        draw_person(ctx, x, f + 22, look_of(L, idx), walk=u * 10, moving=1.0, basket=out,
                    a=1 - ease(clamp01((u - 0.45) / 0.55)))
    return st


def draw_you_marks(ctx, L, tau, t, lay, a=1.0):
    """「あなた」の字と、レジに着いたときの赤丸（画面の座標で）"""
    st = lane_state(L, tau)
    f = LANE_Y[L]
    x = X0 + slot_of(st, st["n"]) * DX
    xd, yd = to_dev(lay, x - 12, f - 240)
    u = clamp01((t - t_of_tau(sample()["wait"][L])) / 0.35) if st["cur"] >= st["n"] else 0.0
    text(ctx, "あなた", xd, yd, 32 * lay[0], RED, alpha=a * (1 - u))     # レジに着いたら字は消して、赤丸で示す
    if st["cur"] >= st["n"]:
        cx, cy = to_dev(lay, X0 - 6, f - 92)
        note.pen_circle(ctx, cx, cy, 62 * lay[0], 118 * lay[0], RED, seed=80 + (L == "B"), width=6, progress=u, alpha=a)


def draw_pay(ctx, L, tau, lay, a=1.0):
    """支払い中は、レジの客の上に、支払いの方法の札（画面の座標で）"""
    st = lane_state(L, tau)
    c = st["cust"][st["cur"]] if 0 <= st["cur"] < st["n"] else None
    tau = st["tau"]
    if c is None or not (c["P0"] <= tau < c["P1"]):
        return
    u = (tau - c["P0"]) / (c["P1"] - c["P0"])
    b = a * ease_out(u / 0.15) * (1 - ease((u - 0.85) / 0.15))
    x, y = to_dev(lay, (CTR_X0 + CTR_X1) / 2, LANE_Y[L] + CTR_TOP / 2 + 6)   # 台の前の面に出す
    sc = lay[0]
    m = PAY[c["method"]][0]
    w, h = (60 + core.text_width(m, 32)) * sc, 52 * sc
    fill(ctx, (1, 1, 1, 0.92 * b))
    core.rrect(ctx, x - w / 2, y - h / 2, w, h, 10 * sc)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * b))
    ctx.set_line_width(2.2)
    ctx.stroke()
    ix = x - w / 2 + 22 * sc                          # 小さな絵: 現金＝硬貨、カード＝カード、QR・IC＝スマホ
    if m == "現金":
        for ox, oy in ((0, 4), (6, -3)):
            fill(ctx, hexrgb("#f2c14e", b))
            ctx.arc(ix + ox * sc, y + oy * sc, 9 * sc, 0, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * b))
            ctx.set_line_width(1.5)
            ctx.stroke()
    elif m == "カード":
        fill(ctx, hexrgb("#6fa8dc", b))
        core.rrect(ctx, ix - 12 * sc, y - 8 * sc, 24 * sc, 16 * sc, 3)
        ctx.fill()
    else:
        fill(ctx, hexrgb("#4a4f5c", b))
        core.rrect(ctx, ix - 7 * sc, y - 13 * sc, 14 * sc, 26 * sc, 3)
        ctx.fill()
    text(ctx, m, ix + 20 * sc, y, 32 * sc, INK, align="left", alpha=b)


# ---------- 場面 ----------

def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def lane_tau(L, t):
    return min(tau_of(t), sample()["wait"][L])


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    lay = layout(t)
    ctx.push_group()
    ctx.save()
    apply_layout(ctx, lay)
    for L in "AB":
        f = LANE_Y[L]
        note.pen_line(ctx, 60, f + 6, 1040, f + 4, PENCIL, seed=3 + (L == "B"), width=2.5, alpha=0.45)
        draw_lane(ctx, L, lane_tau(L, t), t)
    ctx.restore()
    for L in "AB":
        lane_text(ctx, L, lay)
        draw_pay(ctx, L, lane_tau(L, t), lay)
        draw_you_marks(ctx, L, lane_tau(L, t), t, lay, a=clamp01((t - T_START) / 0.3))   # 列が進み終えてから
    # 冒頭: カゴの点数
    if t < T_GO:
        ta = clamp01((t - 0.8) / 0.3) * (1 - ease((t - T_MOVE + 0.2) / 0.3))
        if ta > 0:
            for L in "AB":
                st = lane_state(L, tau_of(t))
                for i in range(max(0, st["cur"] + 1), LANE_N[L]):
                    x, y = to_dev(lay, X0 + slot_of(st, i) * DX - 21, LANE_Y[L] + 24)
                    text(ctx, f"{LANE_ITEMS[L]}点", x, y, 26, INK, alpha=ta)
                if st["cur"] == 0:
                    x, y = to_dev(lay, IN_X, LANE_Y[L] + 24)
                    text(ctx, f"{LANE_ITEMS[L]}点", x, y, 26, INK, alpha=ta)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def mmss(sec):
    sec = max(0, int(round(sec)))
    return f"{sec // 60}分{sec % 60:02d}秒"


def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    s = sample()
    for L, cx in (("B", 330.0), ("A", 790.0)):
        ink = INK_A if L == "A" else INK_B
        tau = lane_tau(L, t)
        text(ctx, f"{TAG[L]} {LANE_NAME[L]}", cx, 1212, 32, ink, alpha=a)
        ppl, its = ahead_counts(L, tau)
        text(ctx, f"前に {ppl}人・{its}点", cx, 1260, 34, INK, alpha=a)
        done = tau >= s["wait"][L]
        text(ctx, "あなたの番！" if done else "あなたの待ち", cx, 1308, 28, RED if done else PENCIL, bold=done, alpha=a)
        text(ctx, mmss(max(0.0, tau)), cx, 1360, 50, ink if done else INK, alpha=a)
        if done:
            u = clamp01((t - t_of_tau(s["wait"][L])) / 0.3)
            note.pen_circle(ctx, cx, 1360, 140, 40, RED, seed=70 + (L == "B"), width=5, progress=u, alpha=a)
    text(ctx, f"再生 {RACE_X:.0f}倍", 580, 1425, 24, PENCIL, bold=False, alpha=a)
    if t >= T_ENDB:
        b = a * ease_out((t - T_ENDB) / 0.3)
        d = s["wait"]["B"] - s["wait"]["A"]
        note.sticky(ctx, "人が少ない列が\n" + f"{mmss(d)} 早い", 770, 700, 38, "yellow", fg=INK, a=b, tilt=-0.02)


# ---------- 1万回のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results()["m"]
    win = (r["A"]["wait"] < r["B"]["wait"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_B), bgra(COL_A)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win[:m]]
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
    r = results()["m"]
    n = N_TRIAL * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000回", 580, 612, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    win = r["A"]["wait"][:m] < r["B"]["wait"][:m]
    for i, (lab, cnt, col) in enumerate(((f"A {LANE_NAME['B']}が早い", int(m - win.sum()), COL_B),
                                         (f"B {LANE_NAME['A']}が早い", int(win.sum()), COL_A))):
        y = 1200 + i * 60
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(222, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(222, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 272, y, 36, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 36, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。あなたの待ちが短かった列の色", 580, 1330, 26, PENCIL, bold=False, alpha=a)


# ---------- 棒: 待ち時間（同じものさし） ----------
BAR_X0, BAR_LEN, BAR_FULL = 250.0, 560.0, 300.0   # 300秒 → 560px


def bx(sec):
    return BAR_X0 + sec / BAR_FULL * BAR_LEN


def draw_hbar(ctx, y, sec, col, lab, val, a, g=1.0):
    text(ctx, lab, BAR_X0, y - 46, 32, INK, align="left", alpha=a)
    w = (bx(sec) - BAR_X0) * g
    if w > 1:
        ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
        core.rrect(ctx, BAR_X0, y - 20, w, 40, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
        ctx.set_line_width(2.5)
        ctx.stroke()
    tw = core.text_width(val, 36)
    vx = BAR_X0 + w + 14
    if vx + tw > 925:
        vx = BAR_X0 + w - tw - 12
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
    text(ctx, "あなたの待ち時間", 580, 640, 42, INK, alpha=a)
    text(ctx, "（1万回の真ん中の値）", 580, 692, 30, PENCIL, bold=False, alpha=a)
    g1 = ease_out((t - T_BAR - 0.15) / 0.4)
    g2 = ease_out((t - T_BAR - 0.55) / 0.5)
    draw_hbar(ctx, 810, sh["medB"], COL_B, f"A {LANE_NAME['B']}（5人×8点）", mmss(sh["medB"]), a, g1)
    draw_hbar(ctx, 945, sh["medA"], COL_A, f"B {LANE_NAME['A']}（2人×20点）", mmss(sh["medA"]), a, g2)
    if t >= T_REV:
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, "人がふえるたび、あいさつと支払いがふえる", 580, 1110, 34, "pink", fg=RED, a=b, tilt=-0.02)
        b2 = ease_out((t - T_REV - 1.0) / 0.3) * a
        text(ctx, f"1人あたり 約{sh['fixed']:.0f}秒（品物の数によらない）", 580, 1235, 32, INK, bold=False, alpha=b2)


# ---------- ひねり: 人が少ない列の品物をふやす ----------
TW_ROWS = (0, 10, 20, 30, 40)
TW_Y0, TW_DY = 820.0, 98.0
TW_STEP = 0.45


def pct1(p):
    """割合の表示。100% と書かないよう、99.5%以上は切り捨てて小数1桁"""
    if p >= 0.995:
        return f"{min(99.9, math.floor(p * 1000 + 0.5) / 10):.1f}%"
    return f"{int(math.floor(p * 100 + 0.5))}%"


def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + len(TW_ROWS) * TW_STEP + 0.3


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    p = {int(e): float(v) for e, v in zip(EXTRA, sh["pA_extra"])}
    text(ctx, "人が少ない列の 品物を ふやすと", 580, 630, 40, INK, alpha=a)
    text(ctx, "（カゴが軽い列は 5人で40点のまま）", 580, 682, 30, PENCIL, bold=False, alpha=a)
    text(ctx, "人が少ない列が 早かった回", 580, 748, 30, INK_A, alpha=a)
    x0, ln = 300.0, 500.0
    yt, yb = TW_Y0 - 34, TW_Y0 + TW_DY * (len(TW_ROWS) - 1) + 34
    ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
    ctx.set_line_width(3)
    ctx.set_dash([9, 8])
    ctx.move_to(x0 + ln / 2, yt)
    ctx.line_to(x0 + ln / 2, yb)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "半々", x0 + ln / 2, yb + 24, 26, RED, alpha=a)
    for i, e in enumerate(TW_ROWS):
        tk = T_TW_RUN + 0.3 + i * TW_STEP
        if t < tk:
            break
        g = ease_out((t - tk) / 0.35)
        y = TW_Y0 + i * TW_DY
        text(ctx, f"{40 + e}点", x0 - 18, y, 36, INK, align="right", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 20, ln, 40)
        ctx.stroke()
        w = ln * p[e] * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(COL_A, 0.95 * a))
            core.rrect(ctx, x0, y - 20, w, 40, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, pct1(p[e]), x0 + ln + 14, y, 34, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"{sh['be']:.0f}点ふえて、やっと半々", 580, 1290, 36, "yellow", a=b, tilt=-0.02)
    if t >= tb + 0.9:
        b = ease_out((t - tb - 0.9) / 0.3) * a
        note.sticky(ctx, f"1人 ＝ 品物 約{sh['per']:.0f}点ぶん", 580, 1392, 40, "pink", fg=RED, a=b, tilt=0.02)


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


CD_X, CD_Y = 835.0, 850.0


class RIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、レジ2台の列が0秒目から1つ進む"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 60
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (408, 480)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 522, 575 + w2 / 2 + 6, 516, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 562, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 38, 575, 860, gap=40)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 626, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 626, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 626, vs, INK, seed=21 + i, alpha=a * show)
        if t >= self.T_CD[0]:
            a2 = ease_out((t - self.T_CD[0]) / 0.2) * a
            n = sum(1 for c in self.T_CD if c <= t)
            age = t - self.T_CD[n - 1]
            cx, cy = CD_X, CD_Y
            fill(ctx, (*hexrgb(PAPER)[:3], 0.94 * a2))
            core.rrect(ctx, cx - 140, cy - 165, 280, 240, 18)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a2))
            ctx.set_line_width(2.5)
            ctx.stroke()
            note.tape(ctx, cx, cy - 165, 110, 30, -0.04, a=a2)
            note.hand_text(ctx, "予想して！", cx, cy - 108, 42, RED, seed=41, alpha=a2, align="center")
            note.pen_circle(ctx, cx, cy, 58, 56, RED, seed=50 + n, width=6, progress=clamp01(age / 0.3), alpha=a)
            sc = 1 + 0.35 * (1 - ease_out(age / 0.15))
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(sc, sc)
            text(ctx, str(len(self.T_CD) - n), 0, 0, 88, INK, alpha=a)
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
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 36, 540, 840, gap=40)):
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


INTRO = RIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "スタート", 760, 690, 36, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_bars(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "人が少ない列の品物が多かったら？", 580, 860, a=ba, t_rel=t - T_TW, size=44)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め
    if q > 0:
        sh = shown()
        note.sticky(ctx, "セルフレジなら、\n1人は品物 何点ぶん？", 580, 800, 50, "yellow", a=q, tilt=-0.02)
        r = ease_out((t - T_Q - 1.2) / 0.3)
        note.sticky(ctx, f"約{sh['per_self']:.0f}点ぶん（自分で通すと遅いから）", 580, 1010, 38, "pink", fg=RED, a=r, tilt=0.025)
        r2 = ease_out((t - T_Q - 1.7) / 0.3)
        text(ctx, f"店員さんのレジは 約{sh['per']:.0f}点ぶん", 580, 1135, 32, INK, bold=False, alpha=r2)


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
    mx.add(0, pad(DURATION, freqs=(146.8, 220.0, 293.7, 370.0)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for L in "AB":                                    # ピッ（読み取り）と、支払いの終わり（チン）
        for c in s["lanes"][L]:
            for e in c["item_end"]:
                tv = t_of_tau(float(e))
                if tv < T_G0:
                    mx.add(tv, tick(2600.0 if L == "A" else 2300.0, 0.03), 0.10 if tv < T_GO else 0.06)
            tv = t_of_tau(c["P1"])
            if tv < T_G0:
                mx.add(tv, blip(1568.0, 0.12), 0.18)
        mx.add(t_of_tau(s["wait"][L]), bell(784.0 if L == "A" else 659.3, 1.2), 0.45)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_ENDB, bpm=120, vol=0.35)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_BAR + 0.15, blip(587.3, 0.15), 0.35)
    mx.add(T_BAR + 0.55, blip(784.0, 0.15), 0.35)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(len(TW_ROWS)):
        mx.add(T_TW_RUN + 0.3 + i * TW_STEP, blip(523.3 + 60 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.5)
    mx.add(tw_done_t() + 0.9, bell(1046.5, 1.2), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 1.2, bell(880.0, 1.2), 0.45)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    s_mean = sum(SPEED) / 2
    checks = []
    # (1) 対数正規の作り方: 平均と標準偏差が指定どおり
    x = lognorm(np.random.default_rng(1), ITEM_MEAN, ITEM_SD, 400000)
    checks.append(("1点の時間の平均（秒）", float(x.mean()), ITEM_MEAN, 0.01))
    checks.append(("1点の時間の標準偏差（秒）", float(x.std()), ITEM_SD, 0.02))
    # (2) 待ちの平均 = 人数×(その他＋支払い の平均) ＋ 点数の合計×1点の平均×速さの平均（閉じた式）
    for L in "AB":
        exact = LANE_N[L] * mean_fixed() + LANE_N[L] * LANE_ITEMS[L] * ITEM_MEAN * s_mean
        checks.append((f"列{L}の待ちの平均（秒）が式と一致", float(r["m"][L]["wait"].mean()), exact, 0.012 * exact))
    # (3) 2列の差の平均 = 3人ぶんの その他＋支払い（品物の合計が同じなので、品物の分は消える）
    checks.append(("待ちの差の平均（B−A）＝ 3人ぶんの固定の時間", sh["meanB"] - sh["meanA"], 3 * mean_fixed(), 1.0))
    # (4) ひねり: 半々になる点数 ≈ 3人ぶんの固定の時間 ÷ 1点の平均（差の分布がほぼ左右対称なので、平均が0になる所）
    checks.append(("ひねり: 半々になる点数（店員）", sh["be"], 3 * mean_fixed() / (ITEM_MEAN * s_mean), 2.0))
    checks.append(("締め: 半々になる点数（セルフ）", sh["be_self"],
                   3 * mean_fixed(SELF_FIXED) / (ITEM_MEAN * SELF_ITEM * s_mean), 2.0))
    # (5) 品物を足すほど、Aが早い割合は下がる
    checks.append(("ひねり: 足すほど Aが早い割合が下がる", float(np.all(np.diff(sh["pA_extra"]) <= 1e-9)), 1.0, 0.0))
    # (6) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["p_a"])), float(INTRO.correct), 0.0))
    # (7) 見本の待ちが1万回の真ん中の値の近く
    smp = sample()
    checks.append(("見本の待ち A（秒）が真ん中の値の近く", smp["wait"]["A"], sh["medA"], 6.0))
    checks.append(("見本の待ち B（秒）が真ん中の値の近く", smp["wait"]["B"], sh["medB"], 6.0))
    # (8) 画面に出す丸めた点数が、式から出した値の丸めと同じ
    checks.append(("表示: 1人ぶんの点数（店員）の丸め", float(round(sh["per"])),
                   float(round(mean_fixed() / (ITEM_MEAN * s_mean))), 0.0))
    checks.append(("表示: 1人ぶんの点数（セルフ）の丸め", float(round(sh["per_self"])),
                   float(round(mean_fixed(SELF_FIXED) / (ITEM_MEAN * SELF_ITEM * s_mean))), 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.1f}倍  Bの番 {T_ENDB:.2f}秒  見本 {sample()['wait']}")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.3, 0.6, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 16.0, T_ENDB + 0.6, T_G0 + 1.5, T_G1 + 0.5,
              T_BAR + 1.0, T_REV + 1.5, T_TW + 1.0, T_TW_RUN + 1.5, T_TW_RUN + 4.0, T_Q + 0.8, T_Q + 3.0, DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
