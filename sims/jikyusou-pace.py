"""持久走、最初に飛ばす？ 同じペースで走る？ 力が同じ2人で1,500mを1万組。— 2026-10-17 作成（公開予定 10/21）

モデル（体の中の「エネルギーの出どころ」を2つに分けた、よく使われる形。速さの単位は m/秒）
  走るのに要るパワー（1mあたりの消費を1とした「距離ぶん」の単位）:
      P = v × (1 + κ v²) × (1 + η × (1 − W/AC))
      ・v × κ v² は空気抵抗のぶん（力は速さの2乗、パワーは3乗）。Pugh 1971: 中距離の速さでエネルギーの約7.5%。
        その速さを 6 m/秒 と置き、1組ごとに 5〜9% のでたらめ（κ = 割合 ÷ (1−割合) ÷ 36）。
      ・(1 + η(1 − W/AC)) は、余力（W）が減るほど体の効率が落ちるぶん（酸素摂取の「遅い成分」。Jones ほか 2011:
        筋の効率がしだいに落ちること。Skiba ほか 2012: W′ の残りが酸素摂取の上がり方とよく一致）。
        余力0で η 倍ぶん高くつく。η は 5〜11%（走る運動で遅い成分は全体の 8±3%、Mille-Hamard ほか 2026）。
  エネルギーの出どころ:
      ・有酸素（A）: 要るパワーに向かって時定数 τ で追いつく。上限は CP（臨界パワー＝余力を使わずに出し続けられる上限）。
        τ は 20〜40秒（Bailey ほか 2011: 酸素摂取の平均応答時間 35〜42秒。速く入ると短くなる＝飛ばす人に有利なぶん）。
        スタート時の A は CP の 10〜30%（立って待っている状態）。
      ・余力（W、無酸素の貯金。最大 AC）: 要るパワーが A を上回るぶんだけ減る。A を下回れば同じだけ戻る（上限 AC）。
        余力が0になると、A で出せる速さまで落ちる（効率も落ちているので、CP の速さより下になる）。
        これが CP モデル（Monod & Scherrer 1965、W′ は CP より上で使える有限の貯金）を、時間の遅れと効率の低下で広げたもの。
      ※ただの CP モデル（パワー∝速さ・W′一定・遅れなし）では、余力を使い切る限りペース配分によらず時間が同じになる
        （どっちも同じ になるのが式の上で決まっている）。だから上の3つ（空気抵抗・効率の低下・有酸素の遅れ）を入れた。
        3つのうち、有酸素の遅れだけは「飛ばす人に有利」に働く。
  ランナー（1組の2人は同じ力）: CP の速さ 3.0〜4.2 m/秒（1500mで約6〜8分の中高生くらい）、AC 100〜250（m ぶん）。
  走り方:
      同じペース: 余力がちょうどゴールで0になる一定の速さ（その人にとっていちばん速い一定ペース）。
      最初に飛ばす: 最初の 20〜40% の距離を、同じペースの人より 5〜15% 速く。そのあとは、残りの余力がちょうど
                   ゴールで0になる一定の速さ（その人にとって最善の「粘り方」。飛ばす人にいちばん有利な仮定）。
                   飛ばしている間に余力が尽きた人は、そのあと出せるだけの速さで走る。
      最後に飛ばす（ひねり）: 最初の (1−距離の割合) を、同じペースより fast×割合÷(1−割合) だけ遅く。
                   最後の 20〜40% は、残りの余力がちょうどゴールで0になる一定の速さ。
      ゆらぎ: どちらも100mごとに速さが ±1.5%（標準偏差）ずれる。予定どおりには走れない。
  1組ごとに ランナーの力・飛ばし方・空気抵抗・効率の低下・有酸素の遅れ・ゆらぎ を引き直して、1万組。

問い: 「持久走、最初に飛ばす？ / 同じペースで走る？」（2行）  A 少し速めに入る ／ B 同じペース ／ C 最後にスパート
      （2026-10-17 統括の指示で選択肢を言い換え。最初の版は A 同じペース ／ B 最初に飛ばす ／ C どっちも同じ で、答えは B。
        画面で「全力で飛び出す」と誤解されないよう「少し速めに入る」とし、ひねりで計っていた「最後にスパート」を選択肢に入れた。
        モデル・乱数・計算は変えていない。規則は3つの走り方に合わせて書き直した＝下の answer_by_rule）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万組のうち「同じペースの人が先にゴールした組」の割合 p と、タイムの差（飛ばす人 − 同じペースの人）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 1.0秒 なら A、p ≤ 40% かつ g ≤ −1.0秒 なら B、それ以外は C。
結果（SEED_MAIN）: 同じペースが先 24.3%、差の真ん中 −1.6秒（飛ばす人が早い）→ B。
      ※有酸素の遅れの時定数 τ が20〜26秒の組ではほぼ引き分け（同じペースが先 47%・差 −0.1秒）、遅れを外すと同じペースが98%で勝つ。
        答えは τ（息が追いつく速さ）の仮定に強くよる。概要欄にも書く。
ひねり: 「では、最後に飛ばすなら？」 前半をおさえて最後に使い切る人を、同じペースの人と1万組でくらべる。
締め: 「あなたは、最初に飛ばす派だった？」（答えは出さない）

乱数の種は見本（並んで走る2人）の見栄えのために選んでよい。答えの統計は1万組すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "jikyusou-pace"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_PAIR = 10000
DIST = 1500.0                                     # m
SEG = 100.0                                       # ゆらぎの区切り（m）
NOISE_SD = 0.015                                  # 100mごとの速さのゆらぎ（標準偏差）
VC = (3.0, 4.2)                                   # CP の速さ（m/秒）
AC = (100.0, 250.0)                               # 余力の最大（m ぶん）
TAU = (20.0, 40.0)                                # 有酸素が追いつく時定数（秒）
A0 = (0.10, 0.30)                                 # スタート時の有酸素（CP に対する割合）
DRAG6 = (0.05, 0.09)                              # 6 m/秒 での空気抵抗の割合（Pugh 1971: 中距離で約7.5%）
ETA = (0.05, 0.11)                                # 余力0での効率の低下（走る運動の遅い成分 8±3%）
FAST = (0.05, 0.15)                               # 飛ばす大きさ（同じペースより何%速いか）
FRAC = (0.20, 0.40)                               # 飛ばす距離（全体の何%か）
DT = 0.5                                          # 計算のきざみ（秒）
MARK = 10.0                                       # 抜いた地点を調べるきざみ（m）

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 1.0


def beats_even(p_even, gap_med):
    """その走り方が同じペースの人に「はっきり勝つ」: 同じペースが先の組が40%以下で、差の真ん中が1秒以上早い"""
    return p_even <= RULE_LO and gap_med <= -RULE_GAP


def answer_by_rule(p_even, gap_med, p_neg, gap_neg):
    """3つの走り方（A 少し速めに入る ／ B 同じペース ／ C 最後にスパート）のうち、どれがいちばん速いか。
    p_even/gap_med = 少し速めに入る人と同じペースの人、p_neg/gap_neg = 最後にスパートの人と同じペースの人。
    同じペースにはっきり勝つ走り方が1つならそれ、2つなら差の真ん中が大きいほう、どちらも勝たなければ B 同じペース。"""
    f, n = beats_even(p_even, gap_med), beats_even(p_neg, gap_neg)
    if f and n:
        return 0 if gap_med <= gap_neg else 2
    if f:
        return 0                                  # A 少し速めに入る
    if n:
        return 2                                  # C 最後にスパート
    return 1                                      # B 同じペース


# ---------- 体のモデル ----------

def draw_params(rng, n):
    u = lambda lo_hi: rng.uniform(lo_hi[0], lo_hi[1], n)   # noqa: E731
    s6 = u(DRAG6)
    p = dict(vc=u(VC), ac=u(AC), tau=u(TAU), a0=u(A0), kappa=s6 / (1 - s6) / 36.0, eta=u(ETA),
             fast=u(FAST), frac=u(FRAC))
    p["pc"] = p["vc"] * (1 + p["kappa"] * p["vc"] ** 2)
    return p


def econ(v, kappa):
    return v * (1 + kappa * v * v)


def v_of_power(pw, kappa):
    """econ(v) = pw を v について解く（ニュートン法）"""
    v = pw.copy()
    for _ in range(6):
        f = v * (1 + kappa * v * v) - pw
        v = v - f / (1 + 3 * kappa * v * v)
    return v


def aerobic(A, target, p):
    """有酸素の1きざみ: 目標（要るパワー）に時定数 τ で近づく。上限は CP"""
    return np.minimum(A + (target - A) * DT / p["tau"], p["pc"])


def race(p, plan, noise=None, x_start=None, state=None, record=False, t_max=900.0, trace=None):
    """1万組ぶんを同時に走らせる。plan(x) → 目標の速さ（配列）。
    noise: (n, 区間数) の速さの倍率。state: 途中から始めるとき (x, t, A, W)。
    返り値: ゴールの時刻・ゴールでの余力・（record なら）MARK ごとの通過時刻"""
    n = len(p["vc"])
    if state is None:
        x = np.zeros(n)
        t = np.zeros(n)
        A = p["a0"] * p["pc"]
        W = p["ac"].copy()
    else:
        x, t, A, W = (s.copy() for s in state)
    done = x >= DIST
    t_fin = np.where(done, t, np.nan)
    w_fin = np.where(done, W, np.nan)
    marks = None
    if record:
        nm = int(DIST / MARK) + 1
        marks = np.full((n, nm), np.nan)
        marks[:, 0] = 0.0
    k = 0
    while not np.all(done):
        k += 1
        if k * DT > t_max:
            break
        vt = plan(x)
        if noise is not None:
            seg = np.minimum((x // SEG).astype(int), noise.shape[1] - 1)
            vt = vt * noise[np.arange(n), seg]
        fat = 1 + p["eta"] * (1 - np.clip(W, 0, None) / p["ac"])
        need = econ(vt, p["kappa"]) * fat
        # 余力が尽きていたら、有酸素で出せる速さまで落ちる
        empty = (W <= 0) & (need > A)
        v_force = v_of_power(A / fat, p["kappa"])
        v = np.where(empty, np.minimum(vt, v_force), vt)
        need = econ(v, p["kappa"]) * fat
        # 有酸素は要るパワーに向かって追いつく（上限 CP）。余力が尽きて落ちている間も、出そうとしているパワーへ向かう
        A_new = aerobic(A, np.maximum(need, econ(vt, p["kappa"]) * fat), p)
        W_new = np.minimum(W - (need - A) * DT, p["ac"])
        W_new = np.where(empty, np.maximum(W_new, 0.0), W_new)
        x_new = x + v * DT
        act = ~done
        if record:
            m0 = np.floor(x / MARK).astype(int)
            m1 = np.floor(np.minimum(x_new, DIST) / MARK).astype(int)
            hit = act & (m1 > m0)
            for j in np.nonzero(hit)[0]:
                for m in range(m0[j] + 1, m1[j] + 1):
                    marks[j, m] = t[j] + (m * MARK - x[j]) / v[j]
        fin = act & (x_new >= DIST)
        t_fin[fin] = t[fin] + (DIST - x[fin]) / v[fin]
        w_fin[fin] = W_new[fin]
        x = np.where(act, x_new, x)
        t = np.where(act, t + DT, t)
        A = np.where(act, A_new, A)
        W = np.where(act, W_new, W)
        done = done | fin
        if trace is not None:                    # 見本の絵のため: 1きざみごとの 時刻・位置・速さ・余力・有酸素
            trace.append((t.copy(), x.copy(), v.copy(), W.copy(), A.copy()))
    return t_fin, w_fin, marks, (x, t, A, W)


def run_until(p, plan, x_stop):
    """x_stop まで走らせて状態を返す（ゆらぎなし。予定を立てるため）"""
    n = len(p["vc"])
    x = np.zeros(n)
    t = np.zeros(n)
    A = p["a0"] * p["pc"]
    W = p["ac"].copy()
    while np.any(x < x_stop):
        act = x < x_stop
        vt = plan(x)
        fat = 1 + p["eta"] * (1 - np.clip(W, 0, None) / p["ac"])
        need = econ(vt, p["kappa"]) * fat
        empty = (W <= 0) & (need > A)
        v = np.where(empty, np.minimum(vt, v_of_power(A / fat, p["kappa"])), vt)
        need = econ(v, p["kappa"]) * fat
        A_new = aerobic(A, np.maximum(need, econ(vt, p["kappa"]) * fat), p)
        W_new = np.minimum(W - (need - A) * DT, p["ac"])
        W_new = np.where(empty, np.maximum(W_new, 0.0), W_new)
        step = np.minimum(v * DT, np.maximum(x_stop - x, 0))
        frac = np.where(v * DT > 0, step / (v * DT), 0)
        x = np.where(act, x + step, x)
        t = np.where(act, t + DT * frac, t)
        A = np.where(act, A + (A_new - A) * frac, A)
        W = np.where(act, W + (W_new - W) * frac, W)
    return (x, t, A, W)


def best_const(p, state=None, iters=20):
    """（state から）ゴールまで一定の速さで走るとき、余力がちょうどゴールで0になる速さ（二分法）"""
    lo = p["vc"] * 0.7
    hi = p["vc"] * 1.6
    # もう余力が尽きている人は、出せるだけの速さで走るのが最善（目標を上げても、有酸素で出せる速さに抑えられる）
    spent = np.zeros(len(lo), bool) if state is None else state[3] <= 0.05
    for _ in range(iters):
        mid = (lo + hi) / 2
        _, w_end, _, _ = race(p, lambda x, v=mid: v, state=state)
        ok = (np.nan_to_num(w_end, nan=-1.0) > 0.05) | spent   # まだ余力が残っている → もっと速くてよい
        lo = np.where(ok, mid, lo)
        hi = np.where(ok, hi, mid)
    return lo


def subset(p, idx):
    return {k: v[idx] for k, v in p.items()}


def run(seed):
    rng = np.random.default_rng(seed)
    p = draw_params(rng, N_PAIR)
    nseg = int(DIST / SEG)
    noise_e = 1 + rng.normal(0, NOISE_SD, (N_PAIR, nseg))
    noise_f = 1 + rng.normal(0, NOISE_SD, (N_PAIR, nseg))
    noise_n = 1 + rng.normal(0, NOISE_SD, (N_PAIR, nseg))
    # 同じペース: 予定（ゆらぎなし）で余力がゴールで0になる速さ
    v_e = best_const(p)
    # 最初に飛ばす: 前半は v_e×(1+fast)、残りは状態から最善の一定ペース
    x_q = DIST * p["frac"]
    v_1 = v_e * (1 + p["fast"])
    plan1 = lambda x: v_1                                   # noqa: E731
    st = run_until(p, plan1, x_q)
    v_2 = best_const(p, state=st)
    # 最後に飛ばす（参考）: 前半を同じだけ遅く（距離の割合はそのまま後ろへ）、最後の frac を最善の一定ペース
    x_nq = DIST * (1 - p["frac"])
    v_n1 = v_e * (1 - p["fast"] * p["frac"] / (1 - p["frac"]))
    st_n = run_until(p, lambda x: v_n1, x_nq)
    v_n2 = best_const(p, state=st_n)
    # 本番（ゆらぎあり）
    t_e, w_e, m_e, _ = race(p, lambda x: v_e, noise=noise_e, record=True)
    t_f, w_f, m_f, _ = race(p, lambda x: np.where(x < x_q, v_1, v_2), noise=noise_f, record=True)
    t_n, w_n, _, _ = race(p, lambda x: np.where(x < x_nq, v_n1, v_n2), noise=noise_n)
    return dict(p=p, v_e=v_e, v_1=v_1, v_2=v_2, v_n1=v_n1, v_n2=v_n2, t_e=t_e, t_f=t_f, t_n=t_n,
                w_e=w_e, w_f=w_f, m_e=m_e, m_f=m_f)


def noises(seed):
    """run() と同じ順に乱数を引き直して、ゆらぎ（同じペース・飛ばす・最後に飛ばす）を返す"""
    rng = np.random.default_rng(seed)
    draw_params(rng, N_PAIR)
    nseg = int(DIST / SEG)
    return [1 + rng.normal(0, NOISE_SD, (N_PAIR, nseg)) for _ in range(3)]


def overtake_at(m_e, m_f):
    """同じペースの人が、飛ばした人の前に最後に出た地点（m）。ずっと前なら 0、一度も前に出なければ nan"""
    lead_f = m_f < m_e                                       # その地点に飛ばす人が先に着いた
    lead_f[:, 0] = True
    n, nm = lead_f.shape
    out = np.full(n, np.nan)
    last_f = nm - 1 - np.argmax(lead_f[:, ::-1], axis=1)     # 飛ばす人が前だった最後の地点
    even_end = ~lead_f[:, -1]
    out[even_end] = (last_f[even_end] + 1) * MARK
    return out


SEED_MAIN = 20261021
_RES = {}


def results():
    if not _RES:
        cache = OUT / "cache" / f"model_{SEED_MAIN}.npz"
        if cache.exists():
            d = dict(np.load(cache, allow_pickle=True))
            d["p"] = d["p"].item()
            _RES["m"] = d
        else:
            r = run(SEED_MAIN)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **{k: v for k, v in r.items() if k != "p"}, p=np.array(r["p"], dtype=object))
            _RES["m"] = r
    return _RES["m"]


def shown():
    r = results()
    t_e, t_f, t_n = r["t_e"], r["t_f"], r["t_n"]
    gap = t_f - t_e
    ov = overtake_at(r["m_e"], r["m_f"])
    win_e = t_e < t_f
    return dict(p_even=float(np.mean(win_e)), n_even=int(win_e.sum()), n_fast=int((t_f < t_e).sum()),
                gap_med=float(np.median(gap)), gap_mean=float(gap.mean()),
                gap_q=np.percentile(gap, [10, 25, 75, 90]),
                med_e=float(np.median(t_e)), med_f=float(np.median(t_f)),
                ov_med=float(np.nanmedian(ov[win_e])) if win_e.any() else float("nan"),
                ov_q=np.nanpercentile(ov[win_e], [25, 75]) if win_e.any() else None,
                ov_last300=float(np.mean(ov[win_e] >= DIST - 300)) if win_e.any() else float("nan"),
                p_neg=float(np.mean(t_e < t_n)), gap_neg_med=float(np.median(t_n - t_e)),
                p_neg_vs_fast=float(np.mean(t_n < t_f)),
                v_e_med=float(np.median(r["v_e"])), v_2_ratio=float(np.median(r["v_2"] / r["v_e"])))


def report():
    sh = shown()
    r = results()
    print(f"同じペースが先 {sh['p_even']:.4f}（{sh['n_even']}組 / 飛ばすが先 {sh['n_fast']}組）  "
          f"差の中央値 {sh['gap_med']:+.2f}秒  平均 {sh['gap_mean']:+.2f}秒  10/25/75/90% {np.round(sh['gap_q'], 2)}")
    print(f"  答え {'ABC'[answer_by_rule(sh['p_even'], sh['gap_med'], sh['p_neg'], sh['gap_neg_med'])]}")
    print(f"タイム中央値 同じ {sh['med_e']:.1f}秒 / 飛ばす {sh['med_f']:.1f}秒   同じペースの速さ中央値 {sh['v_e_med']:.2f} m/秒"
          f"  後半/同じ {sh['v_2_ratio']:.3f}")
    print(f"抜いた地点（同じペースが勝った組）中央値 {sh['ov_med']:.0f}m  25/75% {sh['ov_q']}  残り300m以内 {sh['ov_last300']:.3f}")
    print(f"最後に飛ばす: 同じペースが先 {sh['p_neg']:.4f}  差の中央値（最後−同じ）{sh['gap_neg_med']:+.2f}秒  "
          f"最後に飛ばすが最初に飛ばすより先 {sh['p_neg_vs_fast']:.3f}")
    print("ゴールでの余力の中央値 同じ", np.round(np.nanmedian(r["w_e"]), 2), "飛ばす", np.round(np.nanmedian(r["w_f"]), 2),
          " 未完走", int(np.isnan(r["t_e"]).sum()), int(np.isnan(r["t_f"]).sum()))


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで走る2人）を選ぶ
# =====================================================================
_SAMPLE = None


def _series(tr, j, t_fin):
    """trace から1人ぶんの 時刻・位置・速さ・余力・有酸素 の列（ゴールの瞬間で切る）"""
    ts = [0.0]
    xs = [0.0]
    vs = [float(tr[0][2][j])]
    ws = [None]
    for t, x, v, w, a in tr:
        if ts[-1] >= t_fin - 1e-9:
            break
        if x[j] >= DIST:
            ts.append(float(t_fin))
            xs.append(DIST)
        else:
            ts.append(float(t[j]))
            xs.append(float(x[j]))
        vs.append(float(v[j]))
        ws.append(float(w[j]))
    ws[0] = ws[1]
    return dict(t=np.array(ts), x=np.array(xs), v=np.array(vs), w=np.array(ws), t_fin=float(t_fin))


def sample():
    """見本: 1万組の中から選ぶ（同じ力・同じゆらぎで、1万組の計算そのもの）。
    条件: 結果が1万組の多数派と同じ向きで、タイム差が真ん中の値の近く（±0.25秒）。飛ばし方は範囲の真ん中あたり。
    その中で、とちゅうの差がいちばん開いた回（追い上げが見える回）"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    p = r["p"]
    sh = shown()
    gap = r["t_f"] - r["t_e"]
    sign = np.sign(sh["gap_med"])
    cand = np.nonzero((np.sign(gap) == sign) & (np.abs(gap - sh["gap_med"]) < 0.25)
                      & (np.abs(p["fast"] - 0.10) < 0.02) & (np.abs(p["frac"] - 0.30) < 0.04)
                      & (np.abs(p["vc"] - 3.6) < 0.2))[0][:40]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    ne, nf, _ = noises(SEED_MAIN)
    q = subset(p, cand)
    v_e, v_1, v_2 = r["v_e"][cand], r["v_1"][cand], r["v_2"][cand]
    x_q = DIST * q["frac"]
    tr_e, tr_f = [], []
    t_e, *_ = race(q, lambda x: v_e, noise=ne[cand], trace=tr_e)
    t_f, *_ = race(q, lambda x: np.where(x < x_q, v_1, v_2), noise=nf[cand], trace=tr_f)
    assert np.allclose(t_e, r["t_e"][cand]) and np.allclose(t_f, r["t_f"][cand])   # 1万組の計算と同じ
    best, best_lead = None, -1.0
    for j in range(len(cand)):
        se, sf = _series(tr_e, j, t_e[j]), _series(tr_f, j, t_f[j])
        tt = np.linspace(0, min(t_e[j], t_f[j]), 400)
        lead = np.interp(tt, sf["t"], sf["x"]) - np.interp(tt, se["t"], se["x"])
        if lead.max() > best_lead:
            best, best_lead = (cand[j], se, sf), float(lead.max())
    i, se, sf = best
    se["ac"] = sf["ac"] = float(p["ac"][i])
    _SAMPLE = dict(i=int(i), e=se, f=sf, lead_max=best_lead, gap=float(r["t_f"][i] - r["t_e"][i]),
                   fast=float(p["fast"][i]), frac=float(p["frac"][i]))
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    print("見本", s["i"], "飛ばす", round(s["fast"], 3), "距離", round(s["frac"], 3), "差", round(s["gap"], 2),
          "最大リード", round(s["lead_max"], 1), "m  タイム", round(s["e"]["t_fin"], 1), round(s["f"]["t_fin"], 1))
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
note.DATE = "10.21"                               # 日付欄（公開予定日）

COL_E, INK_E = "#8fbbe8", "#2f63a8"               # B 同じペース（青）
COL_F, INK_F = "#f4ad6a", "#b8601a"               # A 少し速めに入る（橙）
COL_N, INK_N = "#9fd39a", "#2f7d3a"               # C 最後にスパート（ひねり・緑）
TRACK = "#efc2a4"                                 # トラックの土
GRASS = "#cfe8b4"
TREE = "#a8d68f"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_X = 2.0                                     # 冒頭の速さ（実際の2倍）。最初の約17秒ぶん＝60mほど
SLOW_X = 7.0                                      # ゴール前はゆっくり
SLOW_SPAN = 18.0                                  # 先にゴールする人の何秒前（レースの秒）からゆっくりにするか
RACE_LEN = 12.5                                   # T_GO から2人ともゴールするまで（動画の秒）
BIG_Q = ["持久走、最初に飛ばす？", "同じペースで走る？"]
DETAIL = "同じ力の2人で 1,500m"
LABELS = ["少し速めに入る", "同じペース", "最後にスパート"]
CORRECT = 0                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
NAME = {"e": "同じペース", "f": "少し速めに入る"}
TAG = {"e": "B", "f": "A"}
COL = {"e": COL_E, "f": COL_F}
INKC = {"e": INK_E, "f": INK_F}

# 場面（場面の座標: 幅1080・高さ SCENE_H。画面へは layout で縮めて置く）
SCENE_H = 740.0
CX = 580.0                                        # 紙の中心
LANE_FOOT = {"e": 470.0, "f": 702.0}              # 奥のレーン＝同じペース、手前＝最初に飛ばす
TRACK_TOP, TRACK_MID, TRACK_BOT = 262.0, 488.0, 728.0
RUN_H = 230.0                                     # 走る人の高さ（場面の px）
LAY_INTRO = (1.0, 694.0)                          # (縮める倍率, 場面の上端の y)
LAY_RACE = (0.75, 572.0)


def setup():
    global TL, RACE_X, T_FIN1, T_FIN2, T_RACE_END, T_G0, T_G1, T_REV, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    f1, f2 = sorted((s["e"]["t_fin"], s["f"]["t_fin"]))

    def build(rx):
        ts = np.arange(0, 80, 1 / 300)
        tau = np.zeros_like(ts)
        v = 0.0
        for k in range(1, len(ts)):
            t = ts[k]
            if t < T_GO:
                sp = INTRO_X
            else:
                sp = INTRO_X + (rx - INTRO_X) * ease((t - T_GO) / 0.6)
                if v > f1 - SLOW_SPAN:
                    sp = min(sp, SLOW_X)
            v += sp / 300
            tau[k] = v
        return ts, tau

    lo, hi = 5.0, 200.0
    for _ in range(30):
        mid = (lo + hi) / 2
        ts, tau = build(mid)
        t_end = float(np.interp(f2, tau, ts))
        if t_end > T_GO + RACE_LEN:
            lo = mid
        else:
            hi = mid
    RACE_X = hi
    ts, tau = build(RACE_X)
    TL = dict(t=ts, tau=tau)
    T_FIN1 = float(np.interp(f1, tau, ts))
    T_FIN2 = float(np.interp(f2, tau, ts))
    T_RACE_END = T_FIN2 + 2.6                     # ゴールの付箋を読む時間
    T_G0 = T_RACE_END                             # 1万組のマス目
    T_G1 = T_G0 + 2.6
    T_REV = T_G1 + 0.8                            # 答え
    T_TW = T_REV + 4.4                            # ひねり
    T_TW_RUN = T_TW + 2.7
    T_Q = T_TW_RUN + 5.6                          # 締め
    DURATION = T_Q + 4.6


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def speed_now(t):
    """いまの再生の倍率（τ の進み）"""
    return (tau_of(t + 0.02) - tau_of(t - 0.02)) / 0.04 if t > 0.03 else INTRO_X


# ---------- 2人の状態 ----------

def runner(k, tau):
    """τ（レースの秒）での k の位置・速さ・余力（0〜1）・ゴールしたか"""
    s = sample()[k]
    if tau >= s["t_fin"]:
        dt = tau - s["t_fin"]
        x = DIST + 9.0 * (1 - math.exp(-dt / 3.0))  # ゴールのあと、ゆっくり止まる
        return dict(x=x, v=float(s["v"][-1]) * math.exp(-dt / 3.0), w=float(s["w"][-1]) / s["ac"], done=True)
    i = int(np.searchsorted(s["t"], tau, side="right"))
    i = min(max(i, 1), len(s["t"]) - 1)
    x = float(np.interp(tau, s["t"], s["x"]))
    return dict(x=x, v=float(s["v"][i]), w=float(np.interp(tau, s["t"], s["w"])) / s["ac"], done=False)


def cam_of(t):
    """カメラの位置（m）と縮尺（px/m）。2人の真ん中を追い、差が開いたら引く"""
    tau = tau_of(t)
    xe, xf = runner("e", tau)["x"], runner("f", tau)["x"]
    gap = abs(xf - xe)
    pxm = min(20.0, 640.0 / max(gap, 1e-6))
    return (xe + xf) / 2, pxm


# ---------- 場面の置き場所 ----------

def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def to_dev(lay, x, y):
    sc, y0 = lay
    return CX + (x - CX) * sc, y0 + y * sc


# ---------- 絵: 人（ame-hashiru と同じペン描きの線） ----------

def _limb(ctx, pts, w, col, ink=INK, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink, a))
    for dx, dy in ((0.7, -0.5), (-0.6, 0.8)):
        ctx.set_line_width(w + 4.0)
        ctx.move_to(pts[0][0] + dx, pts[0][1] + dy)
        for p in pts[1:]:
            ctx.line_to(p[0] + dx, p[1] + dy)
        ctx.stroke()
    c = hexrgb(col, a) if isinstance(col, str) else (col[0], col[1], col[2], a)
    ctx.set_source_rgba(*c)
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for p in pts[1:]:
        ctx.line_to(*p)
    ctx.stroke()


def _dark(col, k=0.82):
    c = hexrgb(col)
    return (c[0] * k, c[1] * k, c[2] * k, 1.0)


def draw_person(ctx, x, gy, h, col, phase, amp=1.0, a=1.0):
    """横から見た走る人（右向き）。足元が (x, gy)。amp=0 で立ち止まる"""
    if a <= 0:
        return
    s = h / 150.0
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(s, s)
    if a < 1:
        ctx.push_group()
    lean = 0.20 * (0.3 + 0.7 * amp)
    A_leg = 0.80 * amp
    Kb = 1.5
    A_arm = 0.9 * amp
    flex = 1.35
    bob = 4.0 * amp * abs(math.sin(phase))
    hip = (0.0, -72.0 - bob)
    d = (math.sin(lean), -math.cos(lean))
    sh = (hip[0] + 38 * d[0], hip[1] + 38 * d[1])
    hd = (sh[0] + 22 * d[0] + 3, sh[1] + 22 * d[1])

    def leg(j):
        ph = phase + j * math.pi
        a1 = A_leg * math.sin(ph)
        k = Kb * max(0.0, math.cos(ph)) * amp
        knee = (hip[0] + 36 * math.sin(a1), hip[1] + 36 * math.cos(a1))
        b1 = a1 - k
        foot = (knee[0] + 36 * math.sin(b1), knee[1] + 36 * math.cos(b1))
        return [hip, knee, foot, (foot[0] + 10, foot[1] + 1.5)]

    def arm(j):
        ph = phase + (j + 1) * math.pi
        a1 = A_arm * math.sin(ph)
        el = (sh[0] + 22 * math.sin(a1), sh[1] + 22 * math.cos(a1))
        b1 = a1 + flex * (0.35 + 0.65 * amp) * (1.0 if j == 0 else 0.8)
        hand = (el[0] + 20 * math.sin(b1), el[1] + 20 * math.cos(b1))
        return [sh, el, hand]

    ctx.save()                                         # 影
    ctx.scale(1, 0.22)
    ctx.arc(4, 0, 34, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.15, 0.13, 0.1, 0.13)
    ctx.fill()
    dark = _dark(col)
    _limb(ctx, leg(1), 17, dark)
    _limb(ctx, arm(1), 12, dark)
    _limb(ctx, [hip, sh], 29, col)
    ctx.set_source_rgba(*hexrgb(INK))
    ctx.arc(hd[0], hd[1], 18.3, 0, 2 * math.pi)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#fff3df"))
    ctx.arc(hd[0], hd[1], 15.5, 0, 2 * math.pi)
    ctx.fill()
    fill(ctx, "#3a2f2a")                               # 髪
    ctx.arc(hd[0] - 2, hd[1] - 3, 15.5, math.pi * 0.95, math.pi * 1.85)
    ctx.close_path()
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK))                  # 目
    ctx.arc(hd[0] + 8, hd[1] - 1, 2.4, 0, 2 * math.pi)
    ctx.fill()
    _limb(ctx, leg(0), 17, col)
    _limb(ctx, arm(0), 12, col)
    if a < 1:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 絵: トラック（流れる背景） ----------
_RNG = np.random.default_rng(8)
HATCH = [(float(_RNG.uniform(0, 1)), float(_RNG.uniform(TRACK_TOP + 14, TRACK_BOT - 12)), float(_RNG.uniform(-0.6, 0.6)))
         for _ in range(40)]                      # 1区切り（160px）ぶんの土の筋
TREES = [(0.15, 62.0, 95.0), (0.62, 78.0, 120.0)]
SCROLL = None


def build_scroll():
    """背景の流れた量（px）。速すぎると目が追えないので、1秒あたり最大 900px に抑える（看板とゴールは本当の位置）"""
    global SCROLL
    ts = np.arange(0, DURATION + 1, 1 / 120)
    px = np.zeros_like(ts)
    prev = None
    for k, t in enumerate(ts):
        cam, pxm = cam_of(t)
        if prev is not None:
            d = (cam - prev[0]) * pxm
            px[k] = px[k - 1] + min(max(d, 0.0), 900 / 120)
        prev = (cam, pxm)
    SCROLL = dict(t=ts, px=px)


def scroll_px(t):
    return float(np.interp(t, SCROLL["t"], SCROLL["px"]))


def draw_track(ctx, t, cam, pxm):
    off = scroll_px(t)
    fill(ctx, hexrgb(GRASS, 0.55))                     # 芝と土
    ctx.rectangle(0, 205, W, TRACK_TOP - 205)
    ctx.fill()
    fill(ctx, hexrgb(TRACK, 0.75))
    ctx.rectangle(0, TRACK_TOP, W, TRACK_BOT - TRACK_TOP)
    ctx.fill()
    per = 360.0                                        # 木（奥・ゆっくり流れる）
    o = (off * 0.35) % per
    for k in range(-1, 5):
        for u, ry, th in TREES:
            x = k * per + u * per - o
            if -150 < x < W + 150:
                ctx.set_source_rgba(*hexrgb(INK, 0.85))
                ctx.set_line_width(3)
                ctx.move_to(x, 200)
                ctx.line_to(x, 200 - th + 30)
                ctx.stroke()
                fill(ctx, hexrgb(TREE, 0.9))
                ctx.arc(x, 200 - th, ry * 0.8, 0, 2 * math.pi)
                ctx.fill_preserve()
                ctx.set_source_rgba(*hexrgb(INK, 0.8))
                ctx.set_line_width(2.6)
                ctx.stroke()
    o = (off * 0.7) % 70                               # フェンス（中くらいに流れる）
    ctx.set_source_rgba(*hexrgb(INK, 0.75))
    ctx.set_line_width(2.4)
    for y in (168, 206):
        ctx.move_to(0, y)
        ctx.line_to(W, y)
        ctx.stroke()
    for k in range(-1, int(W / 70) + 2):
        x = k * 70 - o
        ctx.move_to(x, 156)
        ctx.line_to(x, 214)
        ctx.stroke()
    per = 160.0                                        # 土の筋（足元と同じ速さで流れる）
    o = off % per
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_width(2.4)
    ctx.set_source_rgba(*hexrgb("#b07a5a", 0.5))
    for k in range(-1, int(W / per) + 2):
        for u, y, sl in HATCH:
            x = k * per + u * per - o
            ctx.move_to(x, y)
            ctx.line_to(x + 14, y + sl * 6)
    ctx.stroke()
    for y in (TRACK_TOP, TRACK_MID, TRACK_BOT):        # レーンの白線
        ctx.set_source_rgba(1, 1, 1, 0.95)
        ctx.set_line_width(8)
        ctx.move_to(0, y)
        ctx.line_to(W, y)
        ctx.stroke()
        note.pen_line(ctx, 0, y + 5, W, y + 4, PENCIL, seed=int(y), width=1.8, alpha=0.5)


def wx(x, cam, pxm):
    """道の位置（m）→ 場面の x"""
    return CX + (x - cam) * pxm


def mark_alpha(t, m):
    """看板を出す濃さ。スタートとゴールはいつも。100mごとの看板は、ゆっくりのときだけ"""
    if m == 0 or m == int(DIST):
        return 1.0
    return clamp01((14.0 - speed_now(t)) / 4.0)


def mark_label(m):
    return "ゴール" if m == int(DIST) else ("スタート" if m == 0 else f"{m}m")


def draw_marks(ctx, t, cam, pxm):
    """スタート・100mごとの看板・ゴールの線（本当の位置）"""
    for m in range(0, int(DIST) + 1, 100):
        x = wx(m, cam, pxm)
        if not -200 < x < W + 200:
            continue
        goal = m == int(DIST)
        if goal:                                       # ゴールは市松の線
            for k in range(int((TRACK_BOT - TRACK_TOP) / 20)):
                fill(ctx, INK if k % 2 == 0 else "#ffffff")
                ctx.rectangle(x - 10, TRACK_TOP + k * 20, 10, 20)
                ctx.fill()
                fill(ctx, "#ffffff" if k % 2 == 0 else INK)
                ctx.rectangle(x, TRACK_TOP + k * 20, 10, 20)
                ctx.fill()
        elif m == 0:
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.rectangle(x - 6, TRACK_TOP, 12, TRACK_BOT - TRACK_TOP)
            ctx.fill()
        a = mark_alpha(t, m)
        if a <= 0:
            continue
        bw = core.text_width(mark_label(m), 40) + 34    # 看板（芝の上に立てる）
        ctx.set_source_rgba(*hexrgb(INK, 0.85 * a))
        ctx.set_line_width(3)
        ctx.move_to(x, TRACK_TOP)
        ctx.line_to(x, 236)
        ctx.stroke()
        fill(ctx, (1, 1, 1, 0.95 * a))
        core.rrect(ctx, x - bw / 2, 178, bw, 58, 8)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(RED if goal else INK, 0.9 * a))
        ctx.set_line_width(3)
        ctx.stroke()


def draw_mark_text(ctx, t, cam, pxm, lay):
    """看板の字（画面の座標。iPhone で切れる位置では出さない）"""
    for m in range(0, int(DIST) + 1, 100):
        a = mark_alpha(t, m)
        if a <= 0:
            continue
        x = wx(m, cam, pxm)
        lab = mark_label(m)
        xd, yd = to_dev(lay, x, 207)
        size = 40 * lay[0]
        w = core.text_width(lab, size)
        if xd - w / 2 < 80 or xd + w / 2 > 1000:
            continue
        text(ctx, lab, xd, yd, size, RED if m == int(DIST) else INK, alpha=a)


def leg_phase(k, t):
    """足の動き（動画の秒で1秒に約1.7周期。速い再生でもぐるぐる回らないように）"""
    return {"e": 0.0, "f": 1.3}[k] + 2 * math.pi * 1.7 * t * (1.08 if k == "f" else 1.0)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    lay = layout(t)
    cam, pxm = cam_of(t)
    tau = tau_of(t)
    ctx.push_group()
    ctx.save()
    sc, y0 = lay
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)
    ctx.rectangle(0, 0, W, SCENE_H)
    ctx.clip()
    draw_track(ctx, t, cam, pxm)
    draw_marks(ctx, t, cam, pxm)
    ctx.restore()
    draw_mark_text(ctx, t, cam, pxm, lay)
    for k in ("e", "f"):                               # レーンの名前（左に固定。走る人はこの上を通る）
        xd, yd = to_dev(lay, 112, LANE_FOOT[k] - 190)
        note.pen_circle(ctx, xd + 20 * lay[0], yd, 22 * lay[0], 22 * lay[0], INKC[k], seed=3 + (k == "f"), width=3.5)
        text(ctx, TAG[k], xd + 20 * lay[0], yd, 34 * lay[0], INKC[k])
        text(ctx, NAME[k], xd + 52 * lay[0], yd, 38 * lay[0], INKC[k], align="left")
    ctx.save()
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)
    ctx.rectangle(0, 0, W, SCENE_H)
    ctx.clip()
    for k in ("e", "f"):
        st = runner(k, tau)
        x = wx(st["x"], cam, pxm)
        amp = 1.0 if not st["done"] else max(0.0, 1 - (tau - sample()[k]["t_fin"]) / 4.0)
        draw_person(ctx, x, LANE_FOOT[k], RUN_H, COL[k], leg_phase(k, t), amp=amp)
    ctx.restore()
    for k in ("e", "f"):                               # 背中のうしろに A・B の丸（どちらがどちらか、いつでも分かるように）
        st = runner(k, tau)
        xd, yd = to_dev(lay, wx(st["x"], cam, pxm) - 62, LANE_FOOT[k] - RUN_H * 0.68)
        r = 21 * sc
        fill(ctx, (1, 1, 1, 0.9))
        ctx.arc(xd, yd, r, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, xd, yd, r, r, INKC[k], seed=13 + (k == "f"), width=3.5)
        text(ctx, TAG[k], xd, yd, 32 * sc, INKC[k])
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def mmss(sec, frac=False):
    if frac:
        sec = max(0.0, sec)
        m = int(sec // 60)
        return f"{m}分{sec - 60 * m:04.1f}秒"
    sec = max(0, int(sec))
    return f"{sec // 60}分{sec % 60:02d}秒"


def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


def gauge(ctx, x, y, w, h, u, col, a):
    """余力のゲージ（横の棒）"""
    ctx.set_source_rgba(*hexrgb(INK, 0.75 * a))
    ctx.set_line_width(2.5)
    core.rrect(ctx, x, y - h / 2, w, h, 6)
    ctx.stroke()
    ww = (w - 6) * clamp01(u)
    if ww > 1:
        fill(ctx, hexrgb(col, 0.95 * a))
        core.rrect(ctx, x + 3, y - h / 2 + 3, ww, h - 6, 4)
        ctx.fill()


def winner():
    s = sample()
    return "f" if s["f"]["t_fin"] < s["e"]["t_fin"] else "e"


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    st = {k: runner(k, tau) for k in ("e", "f")}
    s = sample()
    d = st["f"]["x"] - st["e"]["x"]                    # 差（どちらが何m前か）
    if not (st["e"]["done"] and st["f"]["done"]):
        if abs(d) < 0.5:
            text(ctx, "ならんでいる", 580, 1146, 38, INK, alpha=a)
        else:
            k = "f" if d > 0 else "e"
            text(ctx, f"{TAG[k]}が {abs(d):.0f}m 前", 580, 1146, 38, INKC[k], alpha=a)
    for k, cx in (("f", 330.0), ("e", 800.0)):
        r = st[k]
        text(ctx, f"{TAG[k]} {NAME[k]}", cx, 1200, 34, INKC[k], alpha=a)
        text(ctx, f"{min(r['x'], DIST):,.0f}m", cx, 1252, 48, INK, alpha=a)
        text(ctx, "余力", cx - 120, 1350, 28, INK, alpha=a)
        gauge(ctx, cx - 88, 1350, 210, 28, r["w"], COL[k], a)
        if r["done"]:
            u = clamp01((t - t_of_fin(k)) / 0.35)
            text(ctx, "ゴール！", cx, 1302, 30, RED, alpha=a)
            text(ctx, mmss(s[k]["t_fin"], frac=True), cx, 1410, 44, INKC[k], alpha=a)
            note.pen_circle(ctx, cx, 1410, 140, 38, RED, seed=70 + (k == "f"), width=5, progress=u, alpha=a)
        else:
            text(ctx, f"100mを {100 / max(r['v'], 0.1):.1f}秒", cx, 1302, 30, PENCIL, bold=False, alpha=a)
            text(ctx, mmss(tau), cx, 1410, 44, INK, alpha=a)
    text(ctx, f"再生 {speed_now(t):.0f}倍", 160, 1146, 24, PENCIL, bold=False, align="left", alpha=a)
    if t >= T_FIN2:
        b = a * ease_out((t - T_FIN2 - 0.2) / 0.3)
        w = winner()
        dd = abs(s["f"]["t_fin"] - s["e"]["t_fin"])
        note.sticky(ctx, f"{NAME[w]}が\n{dd:.1f}秒 早くゴール", 580, 830, 44, "yellow", a=b, tilt=-0.02)


# ---------- 1万組のマス目 ----------
G_COLS, G_ROWS, G_CELL = 125, 80, 6
G_X0, G_Y0 = 580 - G_COLS * G_CELL / 2, 650.0
_GRID = {}


def grid_surface(n):
    key = int(n) // G_COLS
    if key in _GRID:
        return _GRID[key]
    if len(_GRID) > 3:
        _GRID.clear()
    r = results()
    win_f = (r["t_f"] < r["t_e"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_E), bgra(COL_F)], np.uint8)
    m = min(N_PAIR, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_f[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_TW) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results()
    n = N_PAIR * clamp01((t - T_G0 - 0.2) / (T_G1 - T_G0 - 0.2))
    surf, _ = grid_surface(n)
    ctx.set_source_surface(surf, G_X0, G_Y0)
    ctx.paint_with_alpha(a)
    ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
    ctx.set_line_width(2.5)
    ctx.rectangle(G_X0 - 4, G_Y0 - 4, G_COLS * G_CELL + 7, G_ROWS * G_CELL + 7)
    ctx.stroke()
    text(ctx, f"{fmt(n)} / 10,000組", 580, 612, 34, INK, alpha=a)
    m = (int(n) // G_COLS) * G_COLS
    win_f = r["t_f"][:m] < r["t_e"][:m]
    for i, (lab, cnt, col) in enumerate(((f"A {NAME['f']}が先にゴール", int(win_f.sum()), COL_F),
                                         (f"B {NAME['e']}が先にゴール", int(m - win_f.sum()), COL_E))):
        y = 1180 + i * 58
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 250, y, 34, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}組", 915, y, 34, INK, align="right", alpha=a)
    text(ctx, "1マス＝1組（同じ力の2人）。先にゴールした人の色", 580, 1294, 26, PENCIL, bold=False, alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"差は 約{abs(sh['gap_med']):.1f}秒。全力ではなく、少しだけ速めに", 580, 1378, 32, "pink",
                    fg=RED, a=b, tilt=-0.015)
        b2 = ease_out((t - T_REV - 1.2) / 0.3) * a          # なぜ（マス目の上に）
        note.sticky(ctx, "走り始めは 息が追いつかない。\n少し速めに入ると、早く追いつく", 580, 890, 36, "yellow", a=b2,
                    tilt=0.02)


# ---------- ひねり: 最後に飛ばすなら？ ----------
TW_ROWS = (("f", "A 少し速めに入る"), ("n", "C 最後にスパート"))
TW_STEP = 0.6


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + len(TW_ROWS) * TW_STEP + 0.5


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    val = {"f": 1 - sh["p_even"], "n": 1 - sh["p_neg"]}
    col = {"f": COL_F, "n": COL_N}
    text(ctx, "同じペースの人に 勝った組（1万組ずつ）", 580, 650, 40, INK, alpha=a)
    text(ctx, "最後にスパート＝前半をおさえて、最後に使い切る", 580, 704, 28, PENCIL, bold=False, alpha=a)
    x0, ln = 300.0, 480.0
    ys = (850.0, 1000.0)
    yt, yb = ys[0] - 40, ys[-1] + 40
    ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
    ctx.set_line_width(3)
    ctx.set_dash([9, 8])
    ctx.move_to(x0 + ln / 2, yt)
    ctx.line_to(x0 + ln / 2, yb)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "半々", x0 + ln / 2, yb + 26, 28, RED, alpha=a)
    for i, ((k, lab), y) in enumerate(zip(TW_ROWS, ys)):
        tk = T_TW_RUN + 0.3 + i * TW_STEP
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0, y - 52, 34, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 22, ln, 44)
        ctx.stroke()
        w = ln * val[k] * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col[k], 0.95 * a))
            core.rrect(ctx, x0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, pct_i(val[k]), x0 + ln + 16, y, 38, INK, align="left", alpha=a * clamp01(g * 3 - 2))
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"最後にスパートは 約{sh['gap_neg_med']:.1f}秒 おそい", 580, 1170, 34, "pink",
                    fg=RED, a=b, tilt=-0.02)
    if t >= tb + 1.0:
        b = ease_out((t - tb - 1.0) / 0.3) * a
        text(ctx, "前半をゆっくりにすると、息が追いつくのも遅れる", 580, 1285, 30, INK, bold=False, alpha=b)


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


CD_X, CD_Y = 850.0, 890.0


class JIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、トラックを並んで走る2人（0秒目から走っている）"""
    T_DETAIL = 0.8
    T_CHO = (1.5, 1.7, 1.9)
    T_MSG = T_DETAIL
    T_CD = T_CD
    T_MOVE = T_MOVE
    T_GO = T_GO

    def _intro(self, ctx, t, a):
        sz = 62
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 820:
            sz *= 820 / w
        pop = 1 + 0.06 * (1 - ease_out(t / 0.4))
        for line, y in zip(BIG_Q, (410, 484)):
            ctx.save()
            ctx.translate(575, y)
            ctx.scale(pop, pop)
            text(ctx, line, 0, 0, sz, INK, alpha=a)
            ctx.restore()
        w2 = core.text_width(BIG_Q[1], sz)
        note.pen_line(ctx, 575 - w2 / 2 - 6, 526, 575 + w2 / 2 + 6, 520, RED, seed=5, width=7,
                      progress=clamp01(t / 0.5), alpha=a)
        if t >= self.T_DETAIL:
            a1 = ease_out((t - self.T_DETAIL) / 0.25) * a
            text(ctx, DETAIL, 580, 568, 36, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 38, 575, 860)):
            show = ease_out((t - self.T_CHO[i]) / 0.2)
            if show <= 0:
                continue
            x0 += 12 * (1 - show)
            note.pen_circle(ctx, x0 + 27, 632, 27, 27, INK, seed=i + 7, width=4, alpha=a * show)
            text(ctx, "ABC"[i], x0 + 27, 632, 36, INK, alpha=a * show)
            note.hand_text(ctx, v, x0 + 62, 632, vs, INK, seed=21 + i, alpha=a * show)
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
            text(ctx, str(len(self.T_CD) - n), 0, 0, 84, INK, alpha=a)
            ctx.restore()

    def _top(self, ctx, t, m, reveal_t):
        sz = 46
        w = max(core.text_width(l, sz) for l in BIG_Q)
        if w > 850:
            sz *= 850 / w
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


INTRO = JIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "1,500m 走りきるまで", 720, 700, 34, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、最後にスパートなら？", 580, 860, a=ba, t_rel=t - T_TW, size=50)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\n最初に飛ばす派だった？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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

def t_of_fin(k):
    return float(np.interp(sample()[k]["t_fin"], TL["tau"], TL["t"]))


def build_audio():
    s = sample()
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for k, f0 in (("e", 900.0), ("f", 760.0)):        # 足音（足の動きと同じ周期。速い再生の間は鳴らさない）
        rate = 2 * 1.7 * (1.08 if k == "f" else 1.0)
        tt = 0.05 + (0.0 if k == "e" else 0.13)
        while tt < T_G0:
            if (tt < T_GO or speed_now(tt) < 10) and tau_of(tt) < s[k]["t_fin"]:
                mx.add(tt, thump(0.12) * 0.5 + np.pad(tick(f0, 0.02), (0, int(SR * 0.1))), 0.10)
            tt += 1 / rate
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_FIN1 - 1.5, bpm=124, vol=0.35)
    for k in ("e", "f"):
        mx.add(t_of_fin(k), bell(784.0 if k == "f" else 659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万組
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(len(TW_ROWS)):
        mx.add(T_TW_RUN + 0.3 + i * TW_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(tw_done_t(), thump(), 0.45)
    mx.add(T_Q, riser(0.6), 0.35)
    mx.add(T_Q + 0.35, bell(880.0, 1.2), 0.4)
    return mx


# ---------- 照合 ----------

def run_checks():
    sh = shown()
    r = results()
    checks = []
    # (1) ただの CP モデル（空気抵抗・効率の低下・有酸素の遅れなし）では、ペース配分によらずタイムが同じで、
    #     (距離 − AC) ÷ CPの速さ に一致する（この3つを入れた理由の裏づけ）
    rng = np.random.default_rng(5)
    n = 200
    q = draw_params(rng, n)
    q["kappa"][:] = 0
    q["eta"][:] = 0
    q["tau"][:] = DT
    q["a0"][:] = 1.0
    q["pc"] = q["vc"].copy()
    ve = best_const(q)
    st = run_until(q, lambda x: ve * (1 + q["fast"]), DIST * q["frac"])
    v2 = best_const(q, state=st)
    te, *_ = race(q, lambda x: ve)
    tf, *_ = race(q, lambda x: np.where(x < DIST * q["frac"], ve * (1 + q["fast"]), v2))
    theory = (DIST - q["ac"]) / q["vc"]
    checks.append(("ただのCPモデル: 同じペースのタイム − 式（最大のずれ・秒）", float(np.abs(te - theory).max()), 0.0, 0.3))
    checks.append(("ただのCPモデル: 飛ばす − 同じ（最大のずれ・秒）", float(np.abs(tf - te).max()), 0.0, 0.3))
    # (2) 予定（ゆらぎなし）では、どちらの走り方もゴールで余力がほぼ0（使い切る予定になっている）
    idx = np.arange(300)
    p = subset(r["p"], idx)
    _, w_e, *_ = race(p, lambda x: r["v_e"][idx])
    xq = DIST * p["frac"]
    _, w_f, *_ = race(p, lambda x: np.where(x < xq, r["v_1"][idx], r["v_2"][idx]))
    checks.append(("予定どおりなら同じペースの余力はゴールで0（最大・m。きざみ0.5秒の誤差）", float(np.nanmax(np.abs(w_e))), 0.0, 1.5))
    checks.append(("予定どおりなら飛ばす人の余力はゴールで0（最大・m。きざみ0.5秒の誤差）", float(np.nanmax(np.abs(w_f))), 0.0, 1.5))
    # (3) 全員がゴールしている
    checks.append(("1万組すべてゴール（未完走の数）",
                   float(np.isnan(r["t_e"]).sum() + np.isnan(r["t_f"]).sum() + np.isnan(r["t_n"]).sum()), 0.0, 0.0))
    # (4) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["p_even"], sh["gap_med"], sh["p_neg"], sh["gap_neg_med"])),
                   float(INTRO.correct), 0.0))
    # (5) 見本は1万組の中の1組で、結果の向きが多数派と同じ・差が真ん中の値の近く
    smp = sample()
    checks.append(("見本のタイム差（秒）が真ん中の値の近く", smp["gap"], sh["gap_med"], 0.25))
    # (6) 画面の組数が足して1万（同着は無い）
    checks.append(("先にゴールした組の合計", float(sh["n_even"] + sh["n_fast"]), float(N_PAIR), 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    build_scroll()
    report()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.1f}倍  ゴール {T_FIN1:.2f} / {T_FIN2:.2f}秒  答え {T_REV:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 16.0, 18.0, T_FIN1 - 0.5, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_TW + 1.0, T_TW_RUN + 1.5, tw_done_t() + 1.5, T_Q + 1.5,
              DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
