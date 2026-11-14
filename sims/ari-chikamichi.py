"""アリは何匹いれば、近道を見つける？ 巣とえさの間に道が2本。匹数だけ変えて 1万回ずつ。— 2026-10-31 作成（公開予定 11.14・ナレーションなし・45秒前後）

【出典（research/2026-10-31_ari_FACTCHECK.md にまとめた）】
  ・二股の橋の実験: Goss ほか 1989（Naturwissenschaften 76:579）…橋の片方が長い場合。 Deneubourg ほか 1990（J Insect Behav 3:159）…同じ長さの橋。
  ・選ぶ確率の式: P(短い道) = (k+τs)^h / ((k+τs)^h + (k+τl)^h)  τ＝その道を渡ったアリの数（においの量）。k≒20, h≒2 で実験によく合う（Dorigo ほか 2006 が紹介）
  ・においの半減期: 合成フェロモンで約30分、アリのからだから取った抽出物で約4時間（Perna ほか 2012 が Van Vorhis Key らの値として紹介）
  ・「ある数を超えると急に整列」: ファラオアリの群れの大きさでの実験とモデル（Beekman ほか 2001）。アルゼンチンアリでの匹数ごとの実験は見つかっていない → 画面に「計算での見立て」と出す

【計算の前に固定した条件】（この下の数字は 1万回を回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  群れ   : n匹（5・10・20・50・100・200・500）。はじめは全員 巣にいる。巣とえさ場のあいだを 行ったり来たり
           （着いたら 平均W秒 休んで、また出発。出発のときに 道を1本選ぶ）。
  道     : 短い道（長さ Ls = 20〜40 cm の一様）と 長い道（短い道の r倍、r = 1.5〜3 の一様）。歩く速さ v = 0.8〜2.0 cm/秒（一様）。 ← 長さ・速さは出典なしの仮定
           短い道を渡る時間 Ts = Ls / v（約10〜50秒）。長い道は r × Ts。
  休み   : 巣・えさ場で 平均 W 秒（W = 10〜40 の一様。1秒ごとに 1/W の確率で出発）。 ← 仮定
  におい : 道ごとに τ。アリが渡りきるたびに +1（両方向とも）。半減期 H（30分〜4時間を 対数でならして一様）で 少しずつ消える。 ← 出典の2つの値のあいだ
  選び方 : 出発するアリは 短い道を P = (k+τs)^h / ((k+τs)^h + (k+τl)^h) の確率で選ぶ。k = 10〜30（一様, 「約20」のまわり）, h = 1.5〜2.5（一様, 「約2」のまわり）。 ← 幅は仮定
           毎回 少しはでたらめ（確率で選ぶ）。においがまだ無いうちは 半々。
  実験   : 30分（1秒きざみ）。 ← 仮定。比べるのは「最後の2分間」。
  1回ごとに変えるもの: r・Ls・v・W・H・k・h（同じ1万組の条件を 全部の匹数で使い回す＝匹数だけを変えて比べる）。1万回ずつ。

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  最後の2分間に渡りきったアリのうち 近道を通ったものが 8割以上だった回 を「近道にそろった」とする（その2分間に渡りきったアリが6匹未満の回は 判定できないので そろったと数えない）。
  p(n) ＝ 1万回のうち そろった回の割合。 p(n) ≥ 90%（10回に9回）になる 最小の匹数を N* とする。
  N* ≤ 20 → 「10匹くらい」 ／ 21 ≤ N* ≤ 200 → 「50匹くらい」 ／ N* > 200 または届かない → 「500匹くらい」
  【2026-10-31 統括の指示で変更】 はじめの台本は「何匹いれば近道を見つける？」・選択肢 20／100／500匹（N*≤30 → 20、31〜250 → 100、それ以上 → 500）だったが、
  答え（9割を超えるのは50匹から）と選択肢の基準が合わず見えにくいので、問いを「10回に9回、近道にそろうのは何匹から？」・選択肢を 10／50／500匹に変えた。
  しきい値は、感度の結果（N*＝50 か 100 で揺れる）でも答えが変わらない幅に置いた（21〜200 が B）。1万回の計算そのものは変えていない。
  「急に」と言うのは、匹数が隣り合う2点で p が50ポイント以上 跳ねるときだけ。そうでなければ「だんだん」。

【あわせて出す数字】
  ・5匹のとき、そろった回は 1万回のうち何回
  ・ひねり: 遠回りの道にそろった回（最後の2分間に 近道を通ったアリが 2割以下）は 匹数が多くても残るか
  ・見本: 5・20・100・500匹それぞれの「1万回の中の1回」（そのときの多数派の結果で、中央に近い1回）

【絵について】計算は数どおり。絵は 500匹・100匹のとき 一部の匹数だけ描く（アリが重なって見えなくなるため）。道の長さの比は その回の r を そのまま描く。
              見本は 短い道を渡る時間が 32〜48秒、r が 1.75〜2.25 の回から選ぶ（絵で追える速さにするため）。

問い: 「10回に9回、/ 近道にそろうのは / 何匹から？」
      選択肢: 10匹くらい ／ 50匹くらい ／ 500匹くらい（小さい順のまま。正解の記号は 計算のあとで決まる＝run_checks で確かめる）
見せ方: 見本の4コマ（5・20・100・500匹: 早送り → 最後の2分間）→ 匹数ごとの「そろった回の割合」のグラフ →「残念、○が正解」
ひねり: 「では、遠回りにそろう回は？」
締め: 「近道を見つけるのに、あなたなら何匹いると思いましたか？」
言葉: 画面に「計算での見立て」を小さく1回。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "ari-chikamichi"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_RUN = 10000
SEED = 20261114
NS = (5, 10, 20, 50, 100, 200, 500)
N_SHOW = (5, 20, 100, 500)
LB = 200                                             # 道を渡る時間（秒）の上限（長い道は 最大 150秒）
CFG0 = dict(T=1800, win=120, align=0.8, min_cross=6,
            r=(1.5, 3.0), ls=(20.0, 40.0), v=(0.8, 2.0), w=(10.0, 40.0), half=(1800.0, 14400.0),
            k=(10.0, 30.0), h=(1.5, 2.5))
P_STAR = 0.90                                        # 答えの決め方: そろった回が 9割
JUMP = 0.50                                          # 「急に」と言える 隣の点との差


def answer_by_rule(p_by_n):
    """p_by_n: {匹数: そろった回の割合}。戻り値 (key, N*)。key は 'a'（10匹くらい）/'b'（50匹くらい）/'c'（500匹くらい）"""
    ns = sorted(p_by_n)
    nstar = next((n for n in ns if p_by_n[n] >= P_STAR), None)
    if nstar is not None and nstar <= 20:
        return "a", nstar
    if nstar is not None and nstar <= 200:
        return "b", nstar
    return "c", nstar


def sudden(p_by_n):
    """隣り合う2点で p が JUMP 以上跳ねたか。戻り値 (跳ねたか, 最大の跳ね, その左の匹数, 右の匹数)"""
    ns = sorted(p_by_n)
    best = max(range(len(ns) - 1), key=lambda i: p_by_n[ns[i + 1]] - p_by_n[ns[i]])
    d = p_by_n[ns[best + 1]] - p_by_n[ns[best]]
    return d >= JUMP, d, ns[best], ns[best + 1]


def draw_cond(rng, R, cfg=CFG0):
    """1万組の条件（全部の匹数で同じ組を使う）"""
    r = rng.uniform(*cfg["r"], R)
    ls = rng.uniform(*cfg["ls"], R)
    v = rng.uniform(*cfg["v"], R)
    w = rng.uniform(*cfg["w"], R)
    half = np.exp(rng.uniform(math.log(cfg["half"][0]), math.log(cfg["half"][1]), R))
    k = rng.uniform(*cfg["k"], R)
    h = rng.uniform(*cfg["h"], R)
    ts = ls / v
    cs = np.maximum(1, np.rint(ts)).astype(np.int64)
    cl = np.maximum(1, np.rint(r * ts)).astype(np.int64)
    return dict(r=r, ls=ls, v=v, w=w, half=half, k=k, h=h, ts=ts, cs=cs, cl=cl)


def simulate(n, par, rng, cfg=CFG0, rec_idx=None, check=False):
    """n匹の群れの実験を 条件の組の数だけ 同時に回す（1秒きざみ）。戻り値 dict(win_s, win_l, ...)。
    rec_idx があれば その番号の回の 1秒ごとの記録も返す（見本の絵用。乱数は同じ）"""
    R = len(par["cs"])
    T, win = cfg["T"], cfg["win"]
    ar = np.arange(R)
    cs, cl = par["cs"], par["cl"]
    q = 1.0 - np.exp(-1.0 / par["w"])
    dec = np.exp(-math.log(2.0) / par["half"])
    k, he = par["k"], par["h"]
    nest = np.full(R, n, np.int64)
    food = np.zeros(R, np.int64)
    ts_ = np.zeros(R)
    tl_ = np.zeros(R)
    B = np.zeros((2, 2, LB, R), np.int32)             # [道: 0=近道 1=遠回り][向き: 0=巣→えさ 1=えさ→巣][到着の秒 % LB][回]
    win_s = np.zeros(R, np.int32)
    win_l = np.zeros(R, np.int32)
    rec = None
    if rec_idx is not None:
        m = len(rec_idx)
        rec = dict(ts=np.zeros((T, m)), tl=np.zeros((T, m)), nest=np.zeros((T, m), np.int32), food=np.zeros((T, m), np.int32),
                   dep=np.zeros((T, 2, 2, m), np.int32))            # dep[t][道][向き] ＝ その秒に出発した匹数
    for t in range(T):
        i0 = t % LB
        a_s0, a_s1, a_l0, a_l1 = B[0, 0, i0].copy(), B[0, 1, i0].copy(), B[1, 0, i0].copy(), B[1, 1, i0].copy()
        B[0, 0, i0] = 0
        B[0, 1, i0] = 0
        B[1, 0, i0] = 0
        B[1, 1, i0] = 0
        food += a_s0 + a_l0
        nest += a_s1 + a_l1
        ts_ = ts_ * dec + a_s0 + a_s1
        tl_ = tl_ * dec + a_l0 + a_l1
        if t >= T - win:
            win_s += a_s0 + a_s1
            win_l += a_l0 + a_l1
        x = (k + ts_) ** he
        y = (k + tl_) ** he
        ps = x / (x + y)
        dn = rng.binomial(nest, q)
        nest -= dn
        sn = rng.binomial(dn, ps)
        ln = dn - sn
        df = rng.binomial(food, q)
        food -= df
        sf = rng.binomial(df, ps)
        lf = df - sf
        rs, rl = (t + cs) % LB, (t + cl) % LB
        B[0, 0, rs, ar] += sn
        B[1, 0, rl, ar] += ln
        B[0, 1, rs, ar] += sf
        B[1, 1, rl, ar] += lf
        if rec is not None:
            rec["ts"][t], rec["tl"][t] = ts_[rec_idx], tl_[rec_idx]
            rec["nest"][t], rec["food"][t] = nest[rec_idx], food[rec_idx]
            rec["dep"][t, 0, 0], rec["dep"][t, 1, 0] = sn[rec_idx], ln[rec_idx]
            rec["dep"][t, 0, 1], rec["dep"][t, 1, 1] = sf[rec_idx], lf[rec_idx]
    out = dict(win_s=win_s, win_l=win_l)
    if check:
        out["total"] = nest + food + B.sum(axis=(0, 1, 2))
    if rec is not None:
        out["rec"] = rec
    return out


def outcome(win_s, win_l, cfg=CFG0):
    """戻り値 (近道にそろった, 遠回りにそろった, 判定できない, 近道の割合) 各回の配列"""
    tot = win_s + win_l
    judged = tot >= cfg["min_cross"]
    share = win_s / np.maximum(tot, 1)
    return judged & (share >= cfg["align"]), judged & (share <= 1.0 - cfg["align"]), ~judged, share


def run_all(cfg=CFG0, R=N_RUN, seed=SEED):
    par = draw_cond(np.random.default_rng([seed, 0]), R, cfg)
    res = {}
    for n in NS:
        o = simulate(n, par, np.random.default_rng([seed, n]), cfg)
        res[n] = o
    return par, res


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万回ずつ。計算には少し時間がかかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"runs_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        par = {k_[2:]: z[k_] for k_ in z.files if k_.startswith("p_")}
        res = {n: dict(win_s=z[f"s{n}"], win_l=z[f"l{n}"]) for n in NS}
    else:
        import time
        t0 = time.time()
        par, res = run_all()
        print(f"  1万回×{len(NS)}通りの匹数 {time.time() - t0:.0f}秒")
        d = {f"p_{k_}": v_ for k_, v_ in par.items()}
        for n in NS:
            d[f"s{n}"], d[f"l{n}"] = res[n]["win_s"], res[n]["win_l"]
        np.savez_compressed(f, **d)
    st = {}
    for n in NS:
        ok_s, ok_l, unj, share = outcome(res[n]["win_s"], res[n]["win_l"])
        st[n] = dict(p=float(ok_s.mean()), c=int(ok_s.sum()), p_long=float(ok_l.mean()), c_long=int(ok_l.sum()),
                     unj=int(unj.sum()), share=share, ok_s=ok_s, ok_l=ok_l, unj_a=unj,
                     cross=float((res[n]["win_s"] + res[n]["win_l"]).mean()))
    p_by_n = {n: st[n]["p"] for n in NS}
    key, nstar = answer_by_rule(p_by_n)
    _RES["m"] = dict(par=par, res=res, st=st, p_by_n=p_by_n, key=key, nstar=nstar, sud=sudden(p_by_n))
    return _RES["m"]


SENS = (("基準", {}),
        ("実験の長さ 15分", dict(T=900)), ("実験の長さ 60分", dict(T=3600)),
        ("k = 5〜15（約10）", dict(k=(5.0, 15.0))), ("k = 20〜40（約30）", dict(k=(20.0, 40.0))),
        ("h = 1.0〜2.0（約1.5）", dict(h=(1.0, 2.0))), ("h = 2.0〜3.0（約2.5）", dict(h=(2.0, 3.0))),
        ("休み W = 5〜20 秒", dict(w=(5.0, 20.0))), ("休み W = 30〜120 秒", dict(w=(30.0, 120.0))),
        ("消える速さ 半減期 30分だけ", dict(half=(1800.0, 1800.0))), ("消える速さ 半減期 4時間だけ", dict(half=(14400.0, 14400.0))),
        ("r = 1.5〜2.0", dict(r=(1.5, 2.0))), ("r = 2.0〜3.0", dict(r=(2.0, 3.0))),
        ("歩く速さ 0.4〜1.0 cm/秒", dict(v=(0.4, 1.0))),
        ("そろったの基準 7割", dict(align=0.7)), ("そろったの基準 9割", dict(align=0.9)), ("判定の最低 3匹", dict(min_cross=3)))


def sensitivity(R=2500):
    rows = []
    for nm, kw in SENS:
        cfg = dict(CFG0)
        cfg.update(kw)
        par = draw_cond(np.random.default_rng([SEED + 1, 0]), R, cfg)
        pb = {}
        for n in NS:
            o = simulate(n, par, np.random.default_rng([SEED + 1, n]), cfg)
            pb[n] = float(outcome(o["win_s"], o["win_l"], cfg)[0].mean())
        rows.append((nm, pb))
    return rows


def report():
    r = results()
    st = r["st"]
    print(f"乱数の種 {SEED}  {N_RUN}回ずつ  匹数 {NS}  実験 {CFG0['T'] // 60}分（最後の{CFG0['win']}秒を比べる）")
    print("  匹数 | 近道にそろった | 遠回りにそろった | 判定できない | 最後の2分間に渡りきった数（平均）")
    for n in NS:
        s = st[n]
        print(f"  {n:4d} | {s['p'] * 100:6.2f}% ({s['c']:5d}回) | {s['p_long'] * 100:5.2f}% ({s['c_long']:4d}回) | {s['unj']:5d}回 | {s['cross']:.1f}")
    key, ns_ = r["key"], r["nstar"]
    print(f"  N* = {ns_}匹（p ≥ {P_STAR:.0%} になる最小の匹数） → 答え {key}  （a=20匹くらい b=100匹くらい c=500匹くらい）")
    sd, d, n0, n1 = r["sud"]
    print(f"  最大の跳ね: {n0}匹→{n1}匹で {d * 100:.1f}ポイント → {'急に' if sd else 'だんだん'}")
    par = r["par"]
    for nm, a in (("r", par["r"]), ("Ts(秒)", par["ts"]), ("W", par["w"]), ("半減期(分)", par["half"] / 60), ("k", par["k"]), ("h", par["h"])):
        print(f"  条件 {nm}: 平均 {a.mean():.2f}  最小 {a.min():.2f}  最大 {a.max():.2f}")
    for n in (5, 500):
        s = st[n]["share"]
        j = ~st[n]["unj_a"]
        print(f"  {n}匹: 近道の割合の分布（判定できた回）: 10% {np.percentile(s[j], 10):.2f}  50% {np.percentile(s[j], 50):.2f}  90% {np.percentile(s[j], 90):.2f}")
    # 条件ごとの内訳（500匹・5匹）
    for n in (5, 500):
        ok = st[n]["ok_s"]
        for nm, a in (("r", par["r"]), ("h", par["h"]), ("k", par["k"])):
            lo = a < np.median(a)
            print(f"  {n}匹 {nm}が小さい半分: {ok[lo].mean() * 100:.1f}%  大きい半分: {ok[~lo].mean() * 100:.1f}%")


def report_sensitivity():
    print("感度（置き方を変える。各2500回・情報）:")
    for nm, pb in sensitivity():
        key, ns_ = answer_by_rule(pb)
        print(f"  {nm}: " + " ".join(f"{n}:{pb[n] * 100:4.0f}%" for n in NS) + f"  N*={ns_} → {key}")


# ---- MODEL END ----

if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--timing" in sys.argv:
        import time
        t0 = time.time()
        par = draw_cond(np.random.default_rng(1), 2000)
        simulate(100, par, np.random.default_rng(2))
        print(f"2000回×1通り {time.time() - t0:.1f}秒")
        sys.exit(0)
    report()
    if "--nosens" not in sys.argv:
        report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す 4回の実験）を、1万回の中から選ぶ
# =====================================================================
THIN = {5: 1, 20: 1, 100: 4, 500: 20}                # 絵に描くアリの間引き（N匹に1匹）
CS_RANGE = (32, 48)
R_RANGE = (1.75, 2.25)
_SAMPLE = {}


def pick_run(n):
    """そのときの多数派の結果（近道にそろった／遠回りにそろった／ばらばら）の中で、近道の割合が中央に近い1回。
    短い道を渡る時間 32〜48秒・r 1.75〜2.25 の回から選ぶ（絵で追える速さにするため）"""
    r = results()
    par, st = r["par"], r["st"][n]
    share = st["share"]
    mixed = ~st["ok_s"] & ~st["ok_l"] & ~st["unj_a"]
    classes = {"short": st["ok_s"], "long": st["ok_l"], "mixed": mixed}
    modal = max(classes, key=lambda c: int(classes[c].sum()))
    cls = classes[modal]
    med = float(np.median(share[cls]))
    cand = cls & (par["cs"] >= CS_RANGE[0]) & (par["cs"] <= CS_RANGE[1]) & (par["r"] >= R_RANGE[0]) & (par["r"] <= R_RANGE[1])
    ids = np.nonzero(cand)[0]
    h = int(ids[np.argmin(np.abs(share[ids] - med))])
    return h, modal, med


def samples():
    """見本4回（5・20・100・500匹）。同じ乱数で記録し直す（1万回の中の1回そのもの）"""
    if _SAMPLE:
        return _SAMPLE["s"]
    from engine.parts import cache_dir
    r = results()
    par = r["par"]
    picks = {n: pick_run(n) for n in N_SHOW}
    f = cache_dir(SLUG) / f"samples_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        recs = {n: {k_: z[f"{k_}{n}"] for k_ in ("ts", "tl", "nest", "food", "dep")} for n in N_SHOW}
    else:
        recs = {}
        for n in N_SHOW:
            o = simulate(n, par, np.random.default_rng([SEED, n]), rec_idx=[picks[n][0]])
            recs[n] = {k_: v_[..., 0] for k_, v_ in o["rec"].items()}
            assert int(o["win_s"][picks[n][0]]) == int(r["res"][n]["win_s"][picks[n][0]])
        d = {f"{k_}{n}": v_ for n in N_SHOW for k_, v_ in recs[n].items()}
        np.savez_compressed(f, **d)
    T = CFG0["T"]
    out = []
    for n in N_SHOW:
        h, modal, med = picks[n]
        rec = recs[n]
        cs, cl = int(par["cs"][h]), int(par["cl"][h])
        dep = rec["dep"]                                        # (T, 道, 向き)
        flat = dep.reshape(-1)
        idx = np.repeat(np.arange(flat.size), flat)
        rng = np.random.default_rng([SEED, n, 77])
        t_dep = (idx // 4).astype(float)                          # 出発した秒（整数）。位置は (tr - 出発の秒) / 渡る時間
        path = (idx % 4) // 2
        dirn = idx % 2
        keep = rng.random(len(idx)) < 1.0 / THIN[n]
        lat = rng.uniform(-11, 11, len(idx))
        ph = rng.uniform(0, 6.28, len(idx))
        sel = np.nonzero(keep)[0]
        arr_s = np.zeros(T + LB, np.int64)                       # 近道を渡りきった匹数（その秒）
        arr_l = np.zeros(T + LB, np.int64)
        arr_s[cs:cs + T] += dep[:, 0, :].sum(axis=1)
        arr_l[cl:cl + T] += dep[:, 1, :].sum(axis=1)
        ref = max(float(rec["ts"].max()), float(rec["tl"].max()), 1.0)
        out.append(dict(n=n, h=h, modal=modal, med=med, rec=rec, cs=cs, cl=cl, r=float(par["r"][h]), ref=ref,
                        t_dep=t_dep[sel], path=path[sel], dirn=dirn[sel], lat=lat[sel], ph=ph[sel],
                        arr_s=arr_s[:T], arr_l=arr_l[:T], win_s=int(r["res"][n]["win_s"][h]), win_l=int(r["res"][n]["win_l"][h]),
                        share=float(r["st"][n]["share"][h])))
    _SAMPLE["s"] = out
    return out


if __name__ == "__main__" and "--pick" in sys.argv:
    for S in samples():
        print(f"見本 {S['n']}匹: 回 #{S['h']}  多数派 {S['modal']}  近道の割合 {S['share']:.2f}（同じ結果の中央 {S['med']:.2f}）  r={S['r']:.2f}  Ts={S['cs']}秒 長い道 {S['cl']}秒  "
              f"最後の2分 近道{S['win_s']} 遠回り{S['win_l']}  描く出発 {len(S['t_dep'])}")
    sys.exit(0)

# =====================================================================
# ここから下は絵と音
# =====================================================================
import cairo  # noqa: E402

from engine import core, note  # noqa: E402
from engine.note import INK, PENCIL, RED, PAPER  # noqa: E402
from engine.core import (W, H, FPS, Mixer, beat, bell, blip, check_answers, clamp01,  # noqa: E402
                         ease, ease_out, fill, hexrgb, pad, render, riser, rrect, text, thump, tick, whoosh)
from engine.parts import loop_back, stills  # noqa: E402

note.use()
note.DATE = "11.14"                                  # 日付欄（公開予定日）

GROUND_A, GROUND_B = "#dfe9c2", "#c9d9a2"
TRAIL, TRAIL_EDGE = "#f5ecd2", "#cdbf95"
SCENT = "#8a2fb0"                                    # においの色（濃いほど強い）
ANT, ANT_HI, ANT_D = "#c98a4e", "#e6b77f", "#7a4a26"
SOIL, SOIL_D = "#9a6b45", "#5a3b25"

LABELS = ["10匹くらい", "50匹くらい", "500匹くらい"]
KEY_LABEL = {"a": "10匹くらい", "b": "50匹くらい", "c": "500匹くらい"}


def correct_index():
    return LABELS.index(KEY_LABEL[results()["key"]])


BIG_Q3 = ["10回に9回、", "近道にそろうのは", "何匹から？"]                        # 1コマ目の3行
BIG_Q = ["10回に9回、", "近道にそろうのは何匹から？"]                           # 定位置（上）の2行
DETAIL_RULE = "道は2本。「そろう」＝近道を通るアリが8割以上"
DETAIL = "二股の橋の実験をもとにした、計算での見立て"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 880.0, 850.0
CARD_CX = 540.0
CARD_Y_INTRO, CARD_Y_FINAL = 870.0, 590.0
CARD_S_INTRO = 0.80
CD_X, CD_Y = 800.0, 985.0
TL_DUR, LV_DUR, HOLD = 0.7, 2.4, 0.6                # 早送り / 最後の2分間（約50倍速）/ 結果を見せる間
SUB = TL_DUR + LV_DUR + HOLD
INTRO_F = 20.0                                      # 冒頭は 20倍速で はじめの約108秒
BAR_X0, BAR_DX = 200.0, 112.0
BAR_DUR = 2.6
BAR_BASE, BAR_H = 1130.0, 370.0


def setup():
    global T_S, T_G0, T_BARS, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TWB, T_TW2, T_Q, DURATION, SCENES
    T_S = [T_GO + i * SUB for i in range(len(N_SHOW))]     # 見本の4コマの始まり
    T_G0 = T_GO + len(N_SHOW) * SUB                         # グラフ
    T_BARS = T_G0 + 0.8                                     # 棒が伸び始める
    T_DN = T_BARS + BAR_DUR + 0.1                               # 9割そろうのは○匹から
    T_DN2 = T_DN + 2.8                                      # 5匹だと…○回
    T_REV = T_DN2 + 3.0                                     # 答え
    T_ANS2 = T_REV + 2.6                                    # 理由（急に／だんだん）
    T_TW = T_ANS2 + 3.0                                     # ひねり
    T_TWB = T_TW + 0.8                                      # 棒が伸び始める
    T_TW2 = T_TWB + BAR_DUR + 0.2                               # ひねりの答え
    T_Q = T_TW2 + 3.4                                       # 締め
    DURATION = T_Q + 4.2
    SCENES = [("見本の4コマ（5・20・100・500匹）", T_GO, T_G0), ("1万回のグラフ（答え・理由）", T_G0, T_TW),
              ("ひねり（遠回りにそろった回）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def pct(x):
    return int(math.floor(x * 100 + 0.5))


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


# ---------- 絵: アリ ----------

def draw_ant(ctx, x, y, ang, L, ph, carry=False, a=1.0, walk=1.0):
    """かわいい絵柄のアリ（明るい茶色・丸い体・短い脚）。頭が +x。L＝体長 px。walk＝脚を動かす量（0で止まる）"""
    if a <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ang)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.push_group()
    sw = math.sin(ph)
    ctx.set_source_rgba(*hexrgb(ANT_D))
    ctx.set_line_width(max(2.0, L * 0.07))
    for lx, k in ((0.06, 0.0), (-0.10, 1.0)):                    # 脚（短く 2対）
        for sg in (-1, 1):
            sw_ = math.sin(ph + k * 2.1 + (0 if sg > 0 else math.pi)) * walk
            ctx.move_to(lx * L, sg * 0.10 * L)
            ctx.line_to((lx + 0.05 * sw_) * L, sg * 0.27 * L)
            ctx.stroke()
    ctx.set_line_width(max(1.8, L * 0.055))                       # 触角（短く）
    for sg in (-1, 1):
        ctx.move_to(0.38 * L, sg * 0.08 * L)
        ctx.curve_to(0.46 * L, sg * 0.16 * L, 0.52 * L, sg * (0.17 + 0.02 * sw * walk) * L, 0.56 * L, sg * (0.14 + 0.02 * sw * walk) * L)
        ctx.stroke()
    for cx_, rx, ry, col in ((-0.24 * L, 0.27 * L, 0.24 * L, ANT), (0.06 * L, 0.14 * L, 0.13 * L, ANT), (0.30 * L, 0.21 * L, 0.20 * L, ANT)):   # おしり・むね・あたま
        ctx.save()
        ctx.translate(cx_, 0)
        ctx.scale(rx, ry)
        ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(ANT_D, 0.9))
        ctx.set_line_width(max(1.6, L * 0.045))
        ctx.stroke()
    ctx.save()                                                   # おしりのつや
    ctx.translate(-0.27 * L, -0.09 * L)
    ctx.scale(0.12 * L, 0.07 * L)
    ctx.arc(0, 0, 1.0, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(ANT_HI, 0.9))
    ctx.fill()
    for sg in (-1, 1):                                           # 大きな目
        ctx.arc(0.35 * L, sg * 0.09 * L, 0.075 * L, 0, 2 * math.pi)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill()
        ctx.arc(0.365 * L, sg * 0.09 * L, 0.040 * L, 0, 2 * math.pi)
        ctx.set_source_rgba(0.12, 0.08, 0.06, 1)
        ctx.fill()
    if carry:                                                    # えさのかけら（口にくわえる）
        ctx.arc(0.56 * L, 0, 0.11 * L, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#fff1a8"))
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb("#c9a53a"))
        ctx.set_line_width(max(1.2, L * 0.035))
        ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: 地面・道・巣・えさ ----------
PY = 600.0
NEST_C, FOOD_C, MOUND_R = (118.0, PY), (794.0, PY), 64.0
P0, P1 = (176.0, PY), (736.0, PY)
SLANT = 80.0
_GROUND = {}


def ground_surface():
    if "s" in _GROUND:
        return _GROUND["s"]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(CARD_W), int(CARD_H))
    c = cairo.Context(s)
    g = cairo.LinearGradient(0, 0, 0, CARD_H)
    g.add_color_stop_rgb(0, *hexrgb(GROUND_A)[:3])
    g.add_color_stop_rgb(1, *hexrgb(GROUND_B)[:3])
    c.set_source(g)
    c.paint()
    rng = np.random.default_rng(31)
    for _ in range(420):                                       # 土のつぶ
        x, y = rng.uniform(0, CARD_W), rng.uniform(0, CARD_H)
        c.arc(x, y, rng.uniform(1.2, 3.2), 0, 2 * math.pi)
        c.set_source_rgba(*hexrgb("#a9b87f", 0.55))
        c.fill()
    for _ in range(46):                                        # 草
        x, y = rng.uniform(10, CARD_W - 10), rng.uniform(10, CARD_H - 10)
        for dx in (-7, 0, 7):
            c.move_to(x + dx * 0.6, y)
            c.line_to(x + dx, y - rng.uniform(14, 24))
        c.set_source_rgba(*hexrgb("#7da35a", 0.8))
        c.set_line_width(3.0)
        c.set_line_cap(cairo.LINE_CAP_ROUND)
        c.stroke()
    for _ in range(14):                                        # 小石
        x, y = rng.uniform(10, CARD_W - 10), rng.uniform(10, CARD_H - 10)
        c.save()
        c.translate(x, y)
        c.scale(rng.uniform(8, 15), rng.uniform(6, 10))
        c.arc(0, 0, 1.0, 0, 2 * math.pi)
        c.restore()
        c.set_source_rgba(*hexrgb("#b9b8ad", 0.9))
        c.fill_preserve()
        c.set_source_rgba(*hexrgb("#8d8c80", 0.9))
        c.set_line_width(1.6)
        c.stroke()
    for _ in range(7):                                         # 花
        x, y = rng.uniform(20, CARD_W - 20), rng.uniform(20, CARD_H - 20)
        for k in range(5):
            a_ = k * 2 * math.pi / 5
            c.arc(x + 7 * math.cos(a_), y + 7 * math.sin(a_), 5.5, 0, 2 * math.pi)
            c.set_source_rgba(1, 1, 1, 0.95)
            c.fill()
        c.arc(x, y, 4.5, 0, 2 * math.pi)
        c.set_source_rgba(*hexrgb("#f2c230"))
        c.fill()
    _GROUND["s"] = s
    return s


def path_pts(r):
    """近道（まっすぐ）と 遠回り（山なり）の折れ線。遠回りの長さは 近道の r 倍（その回の r をそのまま描く）"""
    D = P1[0] - P0[0]
    hh = math.sqrt(max(((r * D - (D - 2 * SLANT)) / 2.0) ** 2 - SLANT ** 2, 0.0))
    short = np.array([P0, P1], float)
    long_ = np.array([P0, (P0[0] + SLANT, P0[1] - hh), (P1[0] - SLANT, P0[1] - hh), P1], float)
    return short, long_


def poly_info(pts):
    seg = np.diff(pts, axis=0)
    ln = np.hypot(seg[:, 0], seg[:, 1])
    cum = np.concatenate([[0.0], np.cumsum(ln)])
    return pts, cum


def poly_at(info, u):
    """u（0〜1）の位置と進行方向の角度。u は配列でよい"""
    pts, cum = info
    s = np.clip(u, 0.0, 1.0) * cum[-1]
    i = np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(pts) - 2)
    seg = pts[i + 1] - pts[i]
    f = (s - cum[i]) / np.maximum(cum[i + 1] - cum[i], 1e-9)
    xy = pts[i] + seg * f[..., None]
    ang = np.arctan2(seg[..., 1], seg[..., 0])
    return xy[..., 0], xy[..., 1], ang


def stroke_poly(ctx, pts, w, col, a):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(*pts[0])
    for p_ in pts[1:]:
        ctx.line_to(*p_)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def draw_paths(ctx, sh, lg, a_s, a_l):
    """道の色の濃さ＝においの強さ。a_s・a_l は 0〜1"""
    for pts in (sh, lg):
        stroke_poly(ctx, pts, 58, TRAIL_EDGE, 0.9)
        stroke_poly(ctx, pts, 50, TRAIL, 1.0)
    for pts, aa in ((sh, a_s), (lg, a_l)):
        if aa > 0.004:
            stroke_poly(ctx, pts, 50, SCENT, 0.12 + 0.80 * aa)


def draw_mound(ctx, c, r):
    x, y = c
    ctx.save()
    ctx.translate(x, y)
    ctx.arc(0, 0, r, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SOIL))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, SOIL_D, 0.9)
    ctx.arc(0, 0, r * 0.62, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#b88659", 0.9))
    ctx.fill()
    ctx.arc(2, 4, r * 0.34, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#3d2616"))
    ctx.fill()
    ctx.restore()


def draw_food(ctx, c, r):
    x, y = c
    ctx.save()
    ctx.translate(x, y)
    for (dx, dy, rr) in ((r * 0.95, -r * 0.55, 6), (-r * 0.9, r * 0.7, 5), (r * 0.7, r * 0.85, 4), (-r * 0.75, -r * 0.8, 5)):
        ctx.arc(dx, dy, rr, 0, 2 * math.pi)                    # かけら
        ctx.set_source_rgba(*hexrgb("#e6b565"))
        ctx.fill()
    ctx.arc(0, 0, r * 0.88, 0, 2 * math.pi)                    # クッキー
    ctx.set_source_rgba(*hexrgb("#e8b25f"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, "#9a6a25", 0.95)
    for (dx, dy) in ((-0.30, -0.25), (0.28, -0.32), (0.0, 0.05), (-0.28, 0.32), (0.34, 0.26)):
        ctx.arc(dx * r, dy * r, r * 0.11, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#6b3f24"))
        ctx.fill()
    ctx.restore()


# ---------- 絵: 虫めがねの子ども ----------

def draw_kid(ctx, t):
    """カードの左下から のぞきこむ子ども（右＝アリのほうを向く）。虫めがねを持つ"""
    cx, cy = 100.0, 748.0
    bob = 2.0 * math.sin(t * 2.2)
    ctx.save()
    ctx.translate(0, bob)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.new_path()                                              # 体（黄色いカッパ）
    ctx.move_to(cx - 96, CARD_H + 10)
    ctx.curve_to(cx - 96, cy + 70, cx - 62, cy + 52, cx - 20, cy + 52)
    ctx.curve_to(cx + 26, cy + 52, cx + 70, cy + 62, cx + 78, CARD_H + 10)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#f6c63a"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.9)
    for wdt, col in ((30, INK), (23, "#f6c63a")):                # うで（虫めがねへ）
        ctx.move_to(cx + 52, cy + 78)
        ctx.curve_to(cx + 86, cy + 70, cx + 110, cy + 54, cx + 134, cy + 36)
        _stroke(ctx, wdt, col, 0.95)
    ctx.arc(cx + 138, cy + 33, 15, 0, 2 * math.pi)             # 手
    ctx.set_source_rgba(*hexrgb("#f7d3b0"))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    lx, ly = cx + 168, cy - 36                                  # 虫めがね
    ctx.move_to(cx + 140, cy + 28)
    ctx.line_to(lx - 24, ly + 30)
    _stroke(ctx, 11, "#6b4a2c", 1.0)
    ctx.arc(lx, ly, 46, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#dff3ff", 0.55))
    ctx.fill_preserve()
    _stroke(ctx, 9, "#6b4a2c", 1.0)
    ctx.arc(lx - 14, ly - 14, 14, math.pi * 1.05, math.pi * 1.55)
    _stroke(ctx, 5, "#ffffff", 0.9)
    ctx.arc(cx, cy, 52, 0, 2 * math.pi)                         # 頭
    ctx.set_source_rgba(*hexrgb("#f7d3b0"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    ctx.new_path()                                              # かみ
    ctx.arc(cx - 6, cy - 8, 54, math.pi * 0.98, math.pi * 1.98)
    ctx.line_to(cx + 36, cy - 24)
    ctx.curve_to(cx + 14, cy - 36, cx - 18, cy - 30, cx - 48, cy - 12)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb("#5a3a27"))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    ex = cx + 26
    ctx.arc(ex, cy + 6, 8.5, 0, 2 * math.pi)                    # 目（右をのぞく）
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.9)
    ctx.arc(ex + 3, cy + 6, 4.4, 0, 2 * math.pi)
    ctx.set_source_rgba(0.1, 0.08, 0.1, 1)
    ctx.fill()
    ctx.arc(cx + 8, cy + 24, 9, 0.15 * math.pi, 0.85 * math.pi)  # 口
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.arc(cx + 38, cy + 24, 8, 0, 2 * math.pi)                # ほっぺ
    ctx.set_source_rgba(1.0, 0.6, 0.6, 0.55)
    ctx.fill()
    ctx.restore()


# ---------- 見本の状態 ----------

def sample_state(si, tr):
    """見本 si の、実験の tr 秒目（実数）の状態"""
    S = samples()[si]
    rec = S["rec"]
    T = CFG0["T"]
    st = int(min(T - 1, max(0, math.floor(tr))))
    f = min(1.0, max(0.0, tr - st))
    st2 = min(T - 1, st + 1)
    ts = rec["ts"][st] * (1 - f) + rec["ts"][st2] * f
    tl = rec["tl"][st] * (1 - f) + rec["tl"][st2] * f
    td = S["t_dep"]                                              # 道の上のアリ
    lo = int(np.searchsorted(td, tr - S["cl"] - 1.0, side="left"))
    hi = int(np.searchsorted(td, tr, side="right"))
    sl = slice(lo, hi)
    pth, drn = S["path"][sl], S["dirn"][sl]
    c = np.where(pth == 0, S["cs"], S["cl"]).astype(float)
    u = (tr - td[sl]) / c
    ok = (u >= 0) & (u < 1)
    win0 = T - CFG0["win"]
    s_now = int(S["arr_s"][win0:st + 1].sum()) if st >= win0 else 0
    l_now = int(S["arr_l"][win0:st + 1].sum()) if st >= win0 else 0
    return dict(ts=ts, tl=tl, u=u[ok], pth=pth[ok], drn=drn[ok], lat=S["lat"][sl][ok], ph=S["ph"][sl][ok],
                nw=int(round(rec["nest"][st] / THIN[S["n"]])), fw=int(round(rec["food"][st] / THIN[S["n"]])),
                s_now=s_now, l_now=l_now, st=st)


_SLOTS = {}


def slots():
    if "s" not in _SLOTS:
        rng = np.random.default_rng(9)
        k = np.arange(40)
        r_ = 21.0 * np.sqrt(k + 0.6)
        a_ = k * 2.39996 + rng.uniform(-0.2, 0.2, 40)
        _SLOTS["s"] = (r_ * np.cos(a_), r_ * np.sin(a_), rng.uniform(0, 6.28, 40), rng.uniform(0, 6.28, 40))
    return _SLOTS["s"]


def draw_sample(ctx, si, tr, t):
    """見本 si の 絵（地面〜子どもまで）。カード内の座標（0〜CARD_W, 0〜CARD_H）"""
    S = samples()[si]
    s = sample_state(si, tr)
    sh, lg = path_pts(S["r"])
    info_s, info_l = poly_info(sh), poly_info(lg)
    ctx.set_source_surface(ground_surface(), 0, 0)
    ctx.paint()
    ref = S["ref"]
    draw_paths(ctx, sh, lg, min(1.0, s["ts"] / ref) ** 0.8, min(1.0, s["tl"] / ref) ** 0.8)
    draw_mound(ctx, NEST_C, MOUND_R)
    draw_food(ctx, FOOD_C, MOUND_R * 0.86)
    L = {5: 62.0, 20: 58.0, 100: 52.0, 500: 52.0}[S["n"]]
    sx, sy, sa, sp = slots()                                     # 待っているアリ（巣・えさ場のまわり）
    for (c0, cnt, carry) in ((NEST_C, s["nw"], False), (FOOD_C, s["fw"], True)):
        for j in range(min(cnt, 40)):
            wob = 0.8 * math.sin(2.2 * t + sp[j])
            draw_ant(ctx, c0[0] + sx[j] + wob, c0[1] + sy[j], sa[j] + 0.25 * math.sin(1.7 * t + sp[j]), L * 0.9, 3 * t + sp[j], carry=carry, walk=0.35)
    for pidx, info in ((0, info_s), (1, info_l)):                # 歩いているアリ
        for dirn in (0, 1):
            m = (s["pth"] == pidx) & (s["drn"] == dirn)
            if not m.any():
                continue
            uu = s["u"][m] if dirn == 0 else 1.0 - s["u"][m]
            x, y, ang = poly_at(info, uu)
            if dirn == 1:
                ang = ang + math.pi
            nx, ny = -np.sin(ang), np.cos(ang)
            for xi, yi, ai, li, pi_, nxi, nyi in zip(x, y, ang, s["lat"][m], s["ph"][m], nx, ny):
                draw_ant(ctx, float(xi + nxi * li), float(yi + nyi * li), float(ai), L, float(8.0 * tr + pi_ * 3), carry=(dirn == 1))
    draw_kid(ctx, t)
    return s


# ---------- カードと札 ----------

def chip(ctx, s, x, y, size, color=INK, align="left", a=1.0, pad_x=18.0, bold=True):
    w = core.text_width(s, size, bold) + 2 * pad_x
    h = size * 1.25 + 14
    x0 = x if align == "left" else (x - w if align == "right" else x - w / 2)
    rrect(ctx, x0, y - h / 2, w, h, 12)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.94 * a))
    ctx.fill()
    text(ctx, s, x0 + pad_x, y, size, color, align="left", alpha=a, bold=bold)
    return x0, w, h


def sub_index(t):
    return min(len(N_SHOW) - 1, max(0, int((t - T_GO) // SUB)))


def real_time(t):
    """動画の秒 t → (見本の番号, 実験の秒 tr, 場面: 'intro'|'tl'|'live')"""
    T = CFG0["T"]
    if t < T_GO:
        return 0, INTRO_F * t, "intro"
    if t >= T_G0:
        return len(N_SHOW) - 1, float(T), "live"
    i = sub_index(t)
    u = t - T_S[i]
    t0 = INTRO_F * T_GO if i == 0 else 0.0
    if u < TL_DUR:
        return i, t0 + (T - CFG0["win"] - t0) * ease(u / TL_DUR), "tl"
    return i, T - CFG0["win"] + CFG0["win"] * clamp01((u - TL_DUR) / LV_DUR), "live"


def draw_card(ctx, t, m):
    si, tr, mode = real_time(t)
    S = samples()[si]
    s_ = CARD_S_INTRO + (1 - CARD_S_INTRO) * m
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    x0 = CARD_CX - CARD_W * s_ / 2
    ctx.save()
    ctx.translate(x0, y0)
    ctx.scale(s_, s_)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 22)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 10, 10, CARD_W - 20, CARD_H - 20, 16)
    ctx.clip()
    stt = draw_sample(ctx, si, tr, t)
    ctx.restore()
    rrect(ctx, 10, 10, CARD_W - 20, CARD_H - 20, 16)
    _stroke(ctx, 3.2, INK, 0.85)
    sub_a = 1.0 if mode != "intro" else clamp01((m - 0.3) / 0.5)
    if mode != "intro" or m > 0.3:
        chip(ctx, f"アリ {S['n']}匹", 26, 52, 50, INK, a=sub_a)                 # 左上: 匹数
        if THIN[S["n"]] > 1:
            chip(ctx, f"絵は{THIN[S['n']]}匹に1匹", CARD_W - 26, 52, 28, PENCIL, align="right", a=sub_a, bold=False)
        chip(ctx, "巣", NEST_C[0], NEST_C[1] - 100, 28, INK, align="center", a=sub_a)
        chip(ctx, "えさ", FOOD_C[0], FOOD_C[1] - 100, 28, INK, align="center", a=sub_a)
        sh, lg = path_pts(S["r"])
        chip(ctx, "近道", (P0[0] + P1[0]) / 2, P0[1] + 62, 30, INK, align="center", a=sub_a)
        chip(ctx, "遠回り", (P0[0] + P1[0]) / 2, lg[1][1] - 40, 30, INK, align="center", a=sub_a)
        if mode == "tl":
            chip(ctx, f"早送り ▶▶  実験 {int(tr // 60)}分", 350, 752, 34, INK, a=sub_a)
        elif mode == "live":
            chip(ctx, "最後の2分間（約50倍速）", 350, 752, 34, INK, a=sub_a)
            tot = stt["s_now"] + stt["l_now"]
            if tot > 0:
                chip(ctx, f"近道を渡った割合 {pct(stt['s_now'] / tot)}%", 350, 812, 34, RED, a=sub_a)
        if mode != "intro":
            g = cairo.LinearGradient(26, 0, 236, 0)
            g.add_color_stop_rgba(0, *hexrgb(SCENT, 0.12))
            g.add_color_stop_rgba(1, *hexrgb(SCENT, 0.92))
            rrect(ctx, 26, 112, 210, 22, 8)
            ctx.set_source(g)
            ctx.fill()
            text(ctx, "うすい→こい＝においの強さ", 26, 152, 26, INK, align="left", bold=False, alpha=sub_a)
    ctx.restore()
    return mode, tr


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    m = INTRO.moved(t)
    z = 1.0 + 0.32 * (1 - ease(clamp01(t / 1.1)))      # 冒頭: 場面が寄ったところから引く（下端を基準に）
    if T_GO <= t < T_G0:
        i = sub_index(t)
        if i > 0:                                       # 見本が切り替わった直後は ふわっと出す
            a = a * (0.55 + 0.45 * ease((t - T_S[i]) / 0.25))
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


# ---------- グラフ（匹数ごとの そろった回の割合） ----------

def bar_x(i):
    return BAR_X0 + BAR_DX * i


def chart_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def bar_progress(t, t0, i):
    """棒 i の伸び（0〜1）。左から順に伸びる"""
    pr = ease(clamp01((t - t0) / BAR_DUR))
    return ease(clamp01(pr * (len(NS) + 1.4) / 1.4 - i / 1.4))


def draw_chart(ctx, t):
    a = chart_alpha(t)
    if a <= 0:
        return
    r = results()
    text(ctx, "匹数ごとの「近道にそろった回」の割合", 560, 640, 38, INK, alpha=a)
    text(ctx, "1万回ずつ・最後の2分間に 近道を通ったアリが8割以上", 560, 686, 26, PENCIL, bold=False, alpha=a)
    ctx.move_to(130, BAR_BASE)
    ctx.line_to(1000, BAR_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    y90 = BAR_BASE - P_STAR * BAR_H                         # 9割の線
    ctx.set_dash([10, 8])
    ctx.move_to(130, y90)
    ctx.line_to(1000, y90)
    _stroke(ctx, 2.5, RED, 0.7 * a)
    ctx.set_dash([])
    text(ctx, "9割", 100, y90 - 22, 26, RED, alpha=a, bold=False)
    for i, n in enumerate(NS):
        p = r["p_by_n"][n]
        pi_ = bar_progress(t, T_BARS, i)
        hgt = BAR_H * p * pi_
        x = bar_x(i)
        star = (r["nstar"] == n) and t >= T_DN
        rrect(ctx, x - 43, BAR_BASE - hgt, 86, max(hgt, 1.0), 8)
        ctx.set_source_rgba(*hexrgb(SCENT if star else "#9b6fc0", 0.92 * a))
        ctx.fill()
        if pi_ > 0.99:
            text(ctx, f"{pct(p)}%", x, BAR_BASE - hgt - 28, 36, RED if star else INK, alpha=a)
        text(ctx, f"{n}匹", x, BAR_BASE + 38, 34, INK, alpha=a)
        if star:
            note.pen_circle(ctx, x, BAR_BASE - hgt - 28, 56, 34, RED, seed=33, width=5, progress=ease_out((t - T_DN) / 0.4), alpha=a)


# ---------- 答え ----------

def answer_key():
    return results()["key"]


def dn_text():
    r = results()
    if r["nstar"] is None:
        return "500匹でも\n9割にとどかない"
    return f"9割そろうのは\n{r['nstar']}匹から"


def dn2_lines():
    c5 = results()["st"][5]["c"]
    return "5匹だと そろった回は", f"1万回のうち {fmt(c5)}回"


def reason_text():
    r = results()
    sd = r["sud"][0]
    head = "500匹でも、9割にとどかない。" if r["nstar"] is None else f"アリが{r['nstar']}匹いれば、10回に9回は近道にそろう。"
    return head + chr(10) + ("匹数が増えると、急にそろうようになる。" if sd else "匹数が増えるほど、だんだんそろう。")


TW_Q = "では、遠回りにそろう回は？"
TW_MAX = 0.20


def tw_a():
    c500 = results()["st"][500]["c_long"]
    return f"500匹では、遠回りにそろう回は{c500}回。" if c500 == 0 else f"500匹でも、遠回りにそろう回は{c500}回。"


def tw_b():
    r = results()
    return f"5匹では {fmt(r['st'][5]['c_long'])}回、100匹では {fmt(r['st'][100]['c_long'])}回に減る。"


def draw_answer(ctx, t):
    if T_DN <= t < T_REV:
        f = 1 - ease((t - T_REV + 0.12) / 0.12) if t > T_REV - 0.12 else 1.0
        u = ease_out((t - T_DN) / 0.3)
        note.sticky(ctx, dn_text(), 575, 1272, 46, "mint", a=u * f, tilt=-0.015)
        if t >= T_DN2:
            u2 = ease_out((t - T_DN2) / 0.3)
            l1, l2 = dn2_lines()
            text(ctx, l1, 560, 1384, 30, INK, bold=False, alpha=u2 * f)
            text(ctx, l2, 560, 1420, 38, RED, alpha=u2 * f)
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"答えは『{KEY_LABEL[key]}』。", 570, 1262, 40, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 570, 1386, 31, "blue", a=c, tilt=0.012)


# ---------- ひねり ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    r = results()
    note.sticky(ctx, TW_Q, 575, 664, 40, "pink", fg=RED, a=ease_out((t - T_TW - 0.15) / 0.3) * a, tilt=-0.015)
    ctx.move_to(130, BAR_BASE)
    ctx.line_to(1000, BAR_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    for i, n in enumerate(NS):
        s_ = r["st"][n]
        pi_ = bar_progress(t, T_TWB, i)
        x = bar_x(i)
        hgt = BAR_H * min(1.0, s_["p_long"] / TW_MAX) * pi_
        rrect(ctx, x - 43, BAR_BASE - hgt, 86, max(hgt, 1.0), 8)
        ctx.set_source_rgba(*hexrgb("#e08a3c", 0.92 * a))
        ctx.fill()
        if pi_ > 0.99:
            text(ctx, fmt(s_["c_long"]), x, BAR_BASE - hgt - 28, 34, RED, alpha=a)
        text(ctx, f"{n}匹", x, BAR_BASE + 38, 34, INK, alpha=a)
    text(ctx, "遠回りの道にそろった回", 560, 760, 36, INK, alpha=a)
    text(ctx, "棒の上＝1万回のうちの回数（近道が2割以下）", 560, 804, 26, PENCIL, bold=False, alpha=a)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        text(ctx, tw_a(), 570, 1290, 36, RED, alpha=e * a)
        text(ctx, tw_b(), 570, 1362, 32, INK, bold=False, alpha=e * a)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に 地面の上のアリ（0秒目から歩き、場面が寄った所から引く）"""
    T_DETAIL = 0.6
    T_CHO = T_CHO
    T_MSG = 0.6
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = min(big3_size(820.0), 96.0)
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
            text(ctx, DETAIL_RULE, 565, 720, 28, INK, bold=False, alpha=a1)
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


INTRO = SIntro(BIG_Q, LABELS, correct=0, msg="", rule=None)
INTRO.correct = correct_index()


# ---------- 締め（アリの行列） ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "近道を見つけるのに、\nあなたなら何匹いると思いましたか？", 575, 790, 46, "yellow", a=q, tilt=-0.02)
    r_ = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 960, 36, INK, bold=False, alpha=r_)
    ctx.save()
    ctx.push_group()
    rrect(ctx, 130, 1040, 840, 380, 24)
    ctx.clip()
    ctx.translate(130, 1040)
    ctx.set_source_surface(ground_surface(), -20, -300)
    ctx.paint()
    pts = np.array([(20, 280), (250, 190), (590, 190), (820, 280)], float)
    stroke_poly(ctx, pts, 60, TRAIL_EDGE, 0.9)
    stroke_poly(ctx, pts, 52, TRAIL, 1.0)
    stroke_poly(ctx, pts, 52, SCENT, 0.80)
    info = poly_info(pts)
    for k in range(9):
        u = ((t - T_Q) * 0.17 + k / 9.0) % 1.0
        x, y, ang = poly_at(info, np.array([u]))
        draw_ant(ctx, float(x[0]), float(y[0] + (7 if k % 2 else -7)), float(ang[0]), 64.0, 8.0 * t + k, carry=(k % 3 == 0))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    rrect(ctx, 130, 1040, 840, 380, 24)
    _stroke(ctx, 3.5, INK, 0.75 * q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_chart(ctx, t)
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
    mx.add(0, pad(DURATION, freqs=(146.8, 196.0, 246.9, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(6):                                      # 冒頭: ちょこちょこ歩く音
        mx.add(0.1 + 0.35 * i, tick(1800 + 90 * (i % 3), 0.03), 0.30)
    for i, ts_ in enumerate(T_S):                           # 4コマ: 切り替わりの音と、早送り・歩く音
        mx.add(ts_, blip(523.3 * (1.12246 ** (2 * i)), 0.12), 0.35)
        mx.add(ts_, riser(TL_DUR * 0.9), 0.22)
        for j in range(8):
            mx.add(ts_ + TL_DUR + 0.3 * j, tick(1500 + 120 * (j % 3), 0.03), 0.22)
    mx.add(T_G0 - 0.4, riser(0.8), 0.4)                     # グラフ
    beat(mx, T_BARS, T_BARS + BAR_DUR, bpm=132, vol=0.45, accel=True)
    for i in range(len(NS)):
        mx.add(T_BARS + 0.3 * i + 0.3, bell(523.3 * (1.0595 ** (2 * i)), 0.6), 0.28)
    mx.add(T_DN, bell(784.0, 0.9), 0.45)
    mx.add(T_DN2, bell(880.0, 0.9), 0.45)
    mx.add(T_REV, bell(523.3, 1.4), 0.5)
    mx.add(T_REV + 0.3, bell(784.0, 1.4), 0.45)
    mx.add(T_ANS2, blip(587.3, 0.14), 0.3)
    mx.add(T_TW, riser(0.6), 0.35)                          # ひねり
    mx.add(T_TW + 0.3, bell(698.5, 1.0), 0.4)
    beat(mx, T_TWB, T_TWB + BAR_DUR, bpm=132, vol=0.4, accel=True)
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


def _agent_run(n, i, par, rng, cfg=CFG0):
    """アリ1匹ずつの予定表（出発・到着の出来事を時刻順に処理）で 1回の実験を回す。simulate とは別の書き方。
    戻り値 (最後の2分間に近道を渡った数, 遠回りを渡った数)"""
    import heapq
    T, win = cfg["T"], cfg["win"]
    cs, cl = int(par["cs"][i]), int(par["cl"][i])
    q = 1.0 - math.exp(-1.0 / par["w"][i])
    dec = math.exp(-math.log(2.0) / par["half"][i])
    k, he = float(par["k"][i]), float(par["h"][i])
    tau, last = [0.0, 0.0], [0, 0]
    loc = [0] * n                                            # 0=巣 1=えさ場
    ev = []
    for a in range(n):
        t0 = int(rng.geometric(q)) - 1
        if t0 < T:
            heapq.heappush(ev, (t0, 1, a, 0))
    ws = wl = 0
    while ev:
        t, kind, a, p = heapq.heappop(ev)
        if kind == 0:                                        # 到着（その秒の出発より先に処理）
            tau[p] = tau[p] * dec ** (t - last[p]) + 1.0
            last[p] = t
            loc[a] ^= 1
            if t >= T - win:
                if p == 0:
                    ws += 1
                else:
                    wl += 1
            td = t + int(rng.geometric(q)) - 1
            if td < T:
                heapq.heappush(ev, (td, 1, a, 0))
        else:                                                # 出発
            ts_ = tau[0] * dec ** (t - last[0])
            tl_ = tau[1] * dec ** (t - last[1])
            x, y = (k + ts_) ** he, (k + tl_) ** he
            pp = 0 if rng.random() < x / (x + y) else 1
            ta = t + (cs if pp == 0 else cl)
            if ta < T:
                heapq.heappush(ev, (ta, 0, a, pp))
    return ws, wl


def run_checks():
    r = results()
    st, par = r["st"], r["par"]
    checks = []
    R = N_RUN
    # (1) 条件
    for nm, a_, lo, hi in (("r", par["r"], *CFG0["r"]), ("Ls", par["ls"], *CFG0["ls"]), ("v", par["v"], *CFG0["v"]),
                           ("W", par["w"], *CFG0["w"]), ("半減期", par["half"], *CFG0["half"]), ("k", par["k"], *CFG0["k"]), ("h", par["h"], *CFG0["h"])):
        checks.append((f"条件 {nm} は決めた幅の中", float(a_.min() >= lo - 1e-9 and a_.max() <= hi + 1e-9), 1.0, 0.0))
    checks.append(("条件 r の平均 2.25（1.5〜3 の一様）", float(par["r"].mean()), 2.25, 0.03))
    checks.append(("条件 k の平均 20（10〜30 の一様）", float(par["k"].mean()), 20.0, 0.3))
    checks.append(("条件 h の平均 2.0（1.5〜2.5 の一様）", float(par["h"].mean()), 2.0, 0.02))
    checks.append(("長い道を渡る時間は 上限（バッファ）に収まる", float(par["cl"].max() < LB), 1.0, 0.0))
    checks.append(("回数 = 1万（匹数ごと）", float(all(len(st[n]["share"]) == N_RUN for n in NS)), 1.0, 0.0))
    # (2) 数え方の整合
    small = draw_cond(np.random.default_rng(5), 300)
    for n in (5, 50, 500):
        o = simulate(n, small, np.random.default_rng(6), check=True)
        checks.append((f"{n}匹: 巣＋えさ場＋道の上 の合計がいつも {n}（アリが消えも増えもしない）", float((o["total"] == n).all()), 1.0, 0.0))
    for n in NS:
        ok_s, ok_l, unj = st[n]["ok_s"], st[n]["ok_l"], st[n]["unj_a"]
        checks.append((f"{n}匹: そろった・遠回りにそろった・判定できない は重ならない", float(((ok_s.astype(int) + ok_l + unj) <= 1).all()), 1.0, 0.0))
    ps = [r["p_by_n"][n] for n in NS]
    checks.append(("匹数が増えるほど そろった回の割合は（ほぼ）増える（隣との差 -1.5ポイント以内）", float(all(ps[i + 1] >= ps[i] - 0.015 for i in range(len(ps) - 1))), 1.0, 0.0))
    # (3) アリ1匹ずつの別の書き方と照合（5匹・20匹、各600回）
    for n in (5, 20):
        rng = np.random.default_rng(1234 + n)
        cnt_s = cnt_l = cnt_j = 0
        tot_c = 0
        M = 600
        for i in range(M):
            a_, b_ = _agent_run(n, i, par, rng)
            tot_c += a_ + b_
            if a_ + b_ >= CFG0["min_cross"]:
                cnt_j += 1
                sh_ = a_ / (a_ + b_)
                cnt_s += int(sh_ >= CFG0["align"])
                cnt_l += int(sh_ <= 1 - CFG0["align"])
        p_ag, p_v = cnt_s / M, st[n]["p"]
        sig = math.sqrt(max(p_v * (1 - p_v), 0.01) / M)
        checks.append((f"{n}匹: アリ1匹ずつの別の書き方（600回）でも 近道にそろった割合が同じ", p_ag, p_v, 4 * sig + 0.01))
        q_ag, q_v = cnt_l / M, st[n]["p_long"]
        sigl = math.sqrt(max(q_v * (1 - q_v), 0.01) / M)
        checks.append((f"{n}匹: 同じく 遠回りにそろった割合が同じ", q_ag, q_v, 4 * sigl + 0.01))
        checks.append((f"{n}匹: 同じく 最後の2分間に渡った数の平均が同じ", tot_c / M, st[n]["cross"], 0.06 * st[n]["cross"] + 0.5))
    # (4) 答え
    key, nstar = r["key"], r["nstar"]
    checks.append(("N*: p ≥ 90% になる最小の匹数（数え直し）", float(next((n for n in NS if st[n]["c"] / N_RUN >= P_STAR), 0)), float(nstar or 0), 0.0))
    for pb, k_ in (({5: .1, 10: .2, 20: .95, 50: 1, 500: 1}, "a"), ({5: .1, 20: .5, 50: .9, 500: 1}, "b"), ({5: .1, 50: .5, 100: .5, 200: .95, 500: .99}, "b"),
                   ({5: .1, 50: .5, 200: .89, 500: .89}, "c"), ({5: .1, 100: .5, 500: .9}, "c")):
        checks.append((f"規則の道具: N*={next((n for n in sorted(pb) if pb[n] >= P_STAR), None)} → {k_}", float(answer_by_rule(pb)[0] == k_), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("記号の並び: 10匹・50匹・500匹 の小さい順のまま", float(LABELS == ["10匹くらい", "50匹くらい", "500匹くらい"]), 1.0, 0.0))
    checks.append(("画面の正解の記号（0=A 1=B 2=C）は、規則の答えが決めたもの", float(INTRO.correct), float("abc".index(key)), 0.0))
    checks.append(("正解の記号が B（50匹くらい）", float(INTRO.correct), 1.0, 0.0))
    checks.append(("答えの札「50匹くらい」と 理由の札「アリが50匹いれば」が同じ N*", float(KEY_LABEL[key] == "50匹くらい" and nstar == 50 and "50匹いれば" in reason_text() and "50匹から" in dn_text()), 1.0, 0.0))
    sdd = r["sud"]
    checks.append(("「急に」の言い方は 隣の点との差が50ポイント以上のときだけ", float(('急に' in reason_text()) == sdd[0]), 1.0, 0.0))
    checks.append(("遠回りにそろった回は 500匹のとき 100匹以下の回数以下", float(st[500]["c_long"] <= st[100]["c_long"] <= st[5]["c_long"]), 1.0, 0.0))
    # (5) 見本は1万回の中の1回そのもの
    for S in samples():
        n, h = S["n"], S["h"]
        T = CFG0["T"]
        checks.append((f"見本{n}匹: 記録し直した最後の2分間 近道の数 = 1万回の記録", float(S["arr_s"][T - CFG0["win"]:].sum()), float(r["res"][n]["win_s"][h]), 0.0))
        checks.append((f"見本{n}匹: 同じく 遠回りの数", float(S["arr_l"][T - CFG0["win"]:].sum()), float(r["res"][n]["win_l"][h]), 0.0))
        checks.append((f"見本{n}匹: 画面の最後の割合 = 1万回の記録", float(pct(sample_state(samples().index(S), T - 1)["s_now"] / max(1, sample_state(samples().index(S), T - 1)["s_now"] + sample_state(samples().index(S), T - 1)["l_now"]))),
                       float(pct(st[n]["share"][h])), 0.0))
        checks.append((f"見本{n}匹: 短い道を渡る時間 32〜48秒・r 1.75〜2.25", float(32 <= S["cs"] <= 48 and 1.75 <= S["r"] <= 2.25), 1.0, 0.0))
    for si in (0, 1):                                        # 間引きなしの見本: 絵のアリの数 = 巣＋えさ場＋道の上 = n
        S = samples()[si]
        okc = 1.0
        for tr in (30.5, 400.2, 1500.7, 1700.1, 1799.0):
            s_ = sample_state(si, tr)
            if s_["nw"] + s_["fw"] + len(s_["u"]) != S["n"]:
                okc = 0.0
        checks.append((f"見本{S['n']}匹: 画面のアリの数（巣＋えさ場＋道の上）がいつも {S['n']}匹", okc, 1.0, 0.0))
    checks.append(("見本: 100匹・500匹の間引きは 4匹に1匹・20匹に1匹", float(THIN[100] == 4 and THIN[500] == 20), 1.0, 0.0))
    checks.append(("見本: 道の長さの比は その回の r（描いた折れ線の長さ）", float(all(abs(poly_info(path_pts(S["r"])[1])[1][-1] / poly_info(path_pts(S["r"])[0])[1][-1] - S["r"]) < 1e-6 for S in samples())), 1.0, 0.0))
    # (6) 問い
    s3 = min(big3_size(820.0), 96.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    checks.append(("上の問い2行: 文字は24px以上", float(min(56.0, 100.0 * 850.0 / wmax) >= 24), 1.0, 0.0))
    # (7) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本の1コマは どれも 3秒以上", float(SUB >= 3.0), 1.0, 0.0))
    checks.append(("歩く動き: 近道を渡る時間（32秒）は 画面で0.6秒以上", float(32 / (CFG0["win"] / LV_DUR) >= 0.6), 1.0, 0.0))
    checks.append(("数字が見える時間: 9割そろうのは○匹から 3秒以上", float(T_REV - T_DN >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 5匹だと…○回 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: ひねりの棒の数字 3秒以上", float(T_Q - (T_TWB + BAR_DUR) >= 3.0), 1.0, 0.0))
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
    r = results()
    print(f"長さ {DURATION:.1f}秒  見本 {T_GO:.1f}〜{T_G0:.1f}（1コマ {SUB:.1f}秒）  棒 {T_BARS:.1f}  数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    for S in samples():
        print(f"  見本 {S['n']}匹: 回 #{S['h']}  多数派 {S['modal']}  近道 {S['share'] * 100:.0f}%（最後の2分間 近道{S['win_s']}・遠回り{S['win_l']}）  r={S['r']:.2f}  Ts={S['cs']}秒")
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])
    print("  数字の札:", dn_text().replace("\n", ""), "|", " ".join(dn2_lines()), "|", reason_text().replace("\n", ""))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a(), "|", tw_b())
    print(f"  問い3行の文字 {min(big3_size(820.0), 96.0):.0f}px")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_S[0] + 0.3, T_S[0] + 1.5, T_S[0] + 3.0, T_S[1] + 0.2, T_S[1] + 1.8, T_S[1] + 3.0,
              T_S[2] + 1.8, T_S[2] + 3.0, T_S[3] + 1.8, T_S[3] + 3.3, T_G0 + 1.5, T_DN - 0.2, T_DN + 1.2, T_DN2 + 1.2,
              T_REV + 0.9, T_ANS2 + 0.9, T_TW + 0.8, T_TWB + 1.6, T_TW2 + 0.9, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
