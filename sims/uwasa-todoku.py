"""1万人の町で、1人から始めたうわさは何割の人に届く？ 1万回ためす。— 2026-10-31 作成（公開予定 11.16・ナレーションなし・45秒前後）

くらべるのは「1回のうわさで、最後までにうわさを聞いた人の割合 f」。1万回の f の中央値 m で答える。

【計算の前に固定した条件】（この下の数字は 1万回を回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  町     : 1万人（N=10,000）。最初に知っているのは 1人だけ。うわさの中身は 無害（駅前に新しいパン屋ができるらしい、程度）。
  人の状態 : 知らない人（S）／話している人（I）／もう話さない人（R）。
  1日    : 話している人は 1日に C=5 人と話す（5人を基準。ひねりでは 2・5・10人を べつべつに1万回ずつ回す）。
           話す相手は 町の自分以外から でたらめに選ぶ（近所とは限らない。だれとでも会う＝計算での見立て）。
  出会い  : 相手が知らない人 → 相手も話す人になる。
           相手がもう知っている人（話している人・もう話さない人）→ 話しかけた人（自分）が 話すのをやめる。
           （Maki–Thompson 型。Daley–Kendall 型は 2人の話す人が出会うと 2人ともやめる。最後に聞かない人の割合 約20.3% は同じ。Sudbury 1985 / Pittel 1990）
  計算   : 状態の数（S, I）だけを追う確率的な計算（Gillespie 型）。1歩ごとに 話している人の1人が 1回話す。
           次の出会いまでの時間 = 指数分布（割合 C×I /日）。相手が知らない人である確率 = S/(N−1)。
           乱数は 「回の番号・歩数・用途」から決まる 衝突のない乱数（splitmix64）。同じ回は いつでも同じ結果になる（見本の照合のため）。
  1万回  : 乱数の種を変えて 1万回。

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  1万回の f（聞いた人の割合）の中央値を m とする。
  m ≥ 95% → ほぼ全員 ／ 85% ≤ m < 95% → 約9割 ／ m < 85% → 約8割
  （理論の見込み: 聞かないまま 約20.3% → m ≒ 79.7% → 約8割）

【あわせて出す数字】
  ・1万回のばらつき（いちばん届いた回・いちばん届かなかった回）
  ・全員（99%以上）に届いた回は 何回か ／ 最初の数人で止まった回（聞いた人が 100人にも届かず止まった回）は 何回か
  ・見本の1回（1万回の中の1回そのもの）の 聞かなかった人の数
  ・ひねり: 「では、毎日もっと多くの人と話すと？」＝1日に会う人数 2・5・10人 で 1万回ずつ。聞かなかった人の割合の中央値と、町の半分（5,000人）に届くまでの日数の中央値

問い: 「1万人の町で、/ うわさは何割の人に / 届く？」
      選択肢: 約8割 ／ 約9割 ／ ほぼ全員（正解の記号は A。数の3段階は並びを崩さない）
見せ方: 町の通りで2人が立ち話 → 見本の1回（町の家々を上から見た図で、灰色＝知らない人・黄色＝話している人・青＝もう話さない人）→ 1万回の結果の山 →「聞いた人の割合の中央値 m」
ひねり: 「では、毎日もっと多くの人と話すと？」
締め: 「あなたが最後に聞いたうわさは、だれから聞きましたか？」
言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。画面に「計算での見立て」を小さく1回。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "uwasa-todoku"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TOWN = 10000
N_RUN = 10000
SEED_MAIN = 20261116
C_BASE = 5                                           # 1日に話す人数（基準）
C_SHOW = (2, 5, 10)                                  # ひねり
EARLY_N = 100                                        # 「最初の数人で止まった」＝聞いた人が 100人（町の1%）にも届かず止まった
FULL_F = 0.99                                        # 「全員に届いた」＝99%以上
F_ALL, F_NINE = 0.95, 0.85                           # 答えの決め方のしきい値
HALF = N_TOWN // 2

_U64 = np.uint64
_K_RUN = _U64(0xD1B54A32D192ED03)
_K_STEP = _U64(0x9E3779B97F4A7C15)


def answer_by_rule(m):
    """m: 1万回の f（聞いた人の割合）の中央値。戻り値は 'all'（ほぼ全員）/'nine'（約9割）/'eight'（約8割）"""
    if m >= F_ALL:
        return "all"
    if m >= F_NINE:
        return "nine"
    return "eight"


def mix64(x):
    """splitmix64 の混ぜ（uint64 の配列または値）。桁あふれは そのまま回す"""
    with np.errstate(over="ignore"):
        x = x + _U64(0x9E3779B97F4A7C15)
        x = (x ^ (x >> _U64(30))) * _U64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> _U64(27))) * _U64(0x94D049BB133111EB)
        return x ^ (x >> _U64(31))


def run_keys(seed, h):
    """回 h（配列）の乱数の鍵"""
    with np.errstate(over="ignore"):
        return mix64(_U64(seed) * _U64(0x2545F4914F6CDD1D) + np.asarray(h, dtype=np.uint64) * _K_RUN)


def uni(keys, step, k):
    """0〜1 の乱数（開区間）。keys=回ごとの鍵, step=歩数, k=用途（0:時間 1:相手 2:話す人の選び方）"""
    with np.errstate(over="ignore"):
        z = mix64(keys ^ (_U64(step) * _K_STEP + _U64(k + 1) * _U64(0xC2B2AE3D27D4EB4F)))
    return ((z >> _U64(11)).astype(np.float64) + 0.5) * (1.0 / 9007199254740992.0)


def run_many(seed, n, c=C_BASE, n_town=N_TOWN):
    """n回のうわさ（同時に進める）。戻り値: 回ごとの 最後に聞いた人の数 heard・町の半分に届いた時刻 t_half（届かなければ nan）・
    止まった時刻 t_end・話している人の最大数 peak・歩数 steps"""
    keys = run_keys(seed, np.arange(n))
    S = np.full(n, n_town - 1, np.int64)
    I = np.ones(n, np.int64)
    t = np.zeros(n)
    t_half = np.full(n, np.nan)
    t_end = np.full(n, np.nan)
    peak = np.ones(n, np.int64)
    half = n_town // 2
    steps = np.zeros(n, np.int64)
    step = 0
    while True:
        alive = I > 0
        if not alive.any():
            break
        u1 = uni(keys, step, 0)
        u2 = uni(keys, step, 1)
        rate = c * np.maximum(I, 1)
        t = t + np.where(alive, -np.log(u1) / rate, 0.0)
        new = alive & (u2 < S / (n_town - 1.0))
        stop = alive & ~new
        S = S - new
        I = I + new - stop
        steps = steps + alive
        informed = n_town - S
        t_half = np.where(np.isnan(t_half) & alive & (informed >= half), t, t_half)
        t_end = np.where(np.isnan(t_end) & alive & (I == 0), t, t_end)
        peak = np.maximum(peak, I)
        step += 1
    return dict(heard=(n_town - S).astype(np.int32), t_half=t_half, t_end=t_end, peak=peak.astype(np.int32),
                steps=steps.astype(np.int32))


def run_single(seed, h, c=C_BASE, n_town=N_TOWN, track=False):
    """回 h の1回を 1つだけ回す（run_many と同じ乱数・同じ式）。track=True なら 人ごとの「聞いた時刻」「やめた時刻」も記録する。
    人は「聞いた順」の番号 0,1,2,…（0 が最初の1人）"""
    key = run_keys(seed, np.array([h]))
    S, I, t = n_town - 1, 1, 0.0
    t_half = float("nan")
    t_end = float("nan")
    peak = 1
    step = 0
    th = [0.0]
    ts = [float("inf")]
    sp = [0]                                         # 話している人（聞いた順の番号）
    while I > 0:
        u1 = float(uni(key, step, 0)[0])
        u2 = float(uni(key, step, 1)[0])
        t = t + (-np.log(u1) / (c * I))
        if u2 < S / (n_town - 1.0):
            S -= 1
            I += 1
            if track:
                th.append(t)
                ts.append(float("inf"))
                sp.append(len(th) - 1)
        else:
            if track:
                u3 = float(uni(key, step, 2)[0])
                j = min(int(u3 * len(sp)), len(sp) - 1)
                ts[sp[j]] = t
                sp[j] = sp[-1]
                sp.pop()
            I -= 1
        if math.isnan(t_half) and n_town - S >= n_town // 2:
            t_half = t
        if I == 0:
            t_end = t
        peak = max(peak, I)
        step += 1
    out = dict(heard=n_town - S, t_half=t_half, t_end=t_end, peak=peak, steps=step)
    if track:
        out.update(th=np.array(th), ts=np.array(ts))
    return out


def run_agents(seed, n_runs, n_town, c=1):
    """別の書き方: 人を1人ずつ配列で持つ普通のやり方（小さい町で 状態の数だけの計算と 同じ結果になるか照合する）"""
    rng = np.random.default_rng(seed)
    heard = np.zeros(n_runs, np.int64)
    for r in range(n_runs):
        state = np.zeros(n_town, np.int8)            # 0 知らない 1 話している 2 もう話さない
        state[0] = 1
        sp = [0]
        while sp:
            k = int(rng.integers(len(sp)))
            me = sp[k]
            o = int(rng.integers(n_town - 1))
            if o >= me:
                o += 1
            if state[o] == 0:
                state[o] = 1
                sp.append(o)
            else:
                state[me] = 2
                sp[k] = sp[-1]
                sp.pop()
        heard[r] = int((state > 0).sum())
    return heard


def solve_unheard(k=1):
    """理論の見込み（町が大きいとき）: 聞かないまま残る割合 y は (k+1)(1−y) = −ln y の解。k=1 で 約0.2032"""
    lo, hi = 1e-9, 1 - 1e-9
    f = lambda y: (k + 1) * (1 - y) + math.log(y)     # noqa: E731
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid                                  # f は 0 < y < 0.2032 で負、0.2032 < y < 1 で正
        else:
            hi = mid
    return (lo + hi) / 2


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL " + "BEGIN ----")
    b = src.index("# ---- MODEL " + "END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万回のうわさ（基準）と、ひねりの 2・10人。計算には 数十秒かかるので out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"runs_{_model_hash()}.npz"
    if f.exists():
        z = np.load(f)
        by_c = {}
        for c in C_SHOW:
            by_c[c] = {nm: z[f"c{c}_{nm}"] for nm in ("heard", "t_half", "t_end", "peak", "steps")}
    else:
        import time
        t0 = time.time()
        by_c = {}
        for c in C_SHOW:
            seed = SEED_MAIN if c == C_BASE else SEED_MAIN + 1000 * c
            by_c[c] = run_many(seed, N_RUN, c)
            print(f"  1万回（1日に{c}人）{time.time() - t0:.0f}秒")
        np.savez_compressed(f, **{f"c{c}_{nm}": v for c in C_SHOW for nm, v in by_c[c].items()})
    main = by_c[C_BASE]
    fr = main["heard"] / N_TOWN
    _RES["m"] = dict(main=main, by_c=by_c, f=fr, m=float(np.median(fr)))
    return _RES["m"]


def unheard_stats(run):
    f = run["heard"] / N_TOWN
    return dict(med=float(np.median(f)), lo=float(f.min()), hi=float(f.max()),
                full=int((f >= FULL_F).sum()), early=int((run["heard"] < EARLY_N).sum()),
                half_days=float(np.nanmedian(run["t_half"])), n_half=int((~np.isnan(run["t_half"])).sum()),
                sd=float(f.std()))


def report():
    r = results()
    st = unheard_stats(r["main"])
    key = answer_by_rule(r["m"])
    y = solve_unheard()
    print(f"乱数の種 {SEED_MAIN}  {N_RUN}回  町 {N_TOWN}人  1日に {C_BASE}人と話す")
    print(f"  m（聞いた人の割合の中央値）= {r['m'] * 100:.2f}% → {key}   (理論の見込み: 聞かないまま {y * 100:.2f}% → 聞いた {100 - y * 100:.2f}%)")
    print(f"  ばらつき: いちばん届いた回 {st['hi'] * 100:.2f}%  いちばん届かなかった回 {st['lo'] * 100:.2f}%  標準偏差 {st['sd'] * 100:.3f}ポイント")
    print(f"  全員（{FULL_F:.0%}以上）に届いた回 {st['full']}回 / {N_RUN}  聞いた人が {EARLY_N}人にも届かず止まった回 {st['early']}回")
    h = r["main"]["heard"]
    print(f"  聞いた人 100〜5000人で止まった回 {int(((h >= EARLY_N) & (h < HALF)).sum())}回  最小 {int(h.min())}人")
    print(f"  町の半分（{HALF}人）に届いた回 {st['n_half']}回  届くまでの日数の中央値 {st['half_days']:.2f}日  止まるまで 中央値 {np.nanmedian(r['main']['t_end']):.2f}日  話している人の最大 中央値 {int(np.median(r['main']['peak']))}人")
    print("  ひねり（1日に会う人数別）:")
    for c in C_SHOW:
        s_ = unheard_stats(r["by_c"][c])
        print(f"    {c}人: 聞いた割合の中央値 {s_['med'] * 100:.2f}%（聞かなかった {100 - s_['med'] * 100:.2f}%）  最小 {s_['lo'] * 100:.2f}% 最大 {s_['hi'] * 100:.2f}%  半分に届く日数 中央値 {s_['half_days']:.2f}日  止まった回 {s_['early']}")


# ---- MODEL END ----


def final_dist_exact(N=N_TOWN, max_informed=400):
    """情報（MODEL の外）: 最後に聞いた人の数の分布を 式（状態 (聞いた人の数 j, 話している人 i) を1歩ずつ進める）で出す。
    1歩で 話している人の1人が 1人に話す。相手が知らない人の確率 = (N−j)/(N−1)。止まる＝ i が 0 になる。
    聞いた人が max_informed 人を超えたら数えるのをやめる（N が小さければ max_informed=N で全部）。戻り値: {止まったときの聞いた人数: 確率}"""
    cur = {(1, 1): 1.0}                              # (j, i) → 確率。最初の1人
    dead_by_j = {}
    for _ in range(4 * max_informed):
        nxt = {}
        for (j, i), pr in cur.items():
            p_new = (N - j) / (N - 1.0)
            if j + 1 <= max_informed:
                nxt[(j + 1, i + 1)] = nxt.get((j + 1, i + 1), 0.0) + pr * p_new
            if i - 1 == 0:
                dead_by_j[j] = dead_by_j.get(j, 0.0) + pr * (1 - p_new)
            else:
                nxt[(j, i - 1)] = nxt.get((j, i - 1), 0.0) + pr * (1 - p_new)
        cur = nxt
        if not cur:
            break
    return dead_by_j


def early_stop_exact(max_informed=400):
    by = final_dist_exact(N_TOWN, max_informed)
    return sum(by.values()), by


def report_extra():
    p, by = early_stop_exact()
    top = sorted(by.items(), key=lambda kv: -kv[1])[:3]
    print(f"  最初の数人で止まる確率（式で計算・情報）: {p:.3e} → 約{1 / p:,.0f}回に1回  いちばん多いのは 聞いた人 {top[0][0]}人で止まる（{top[0][1]:.2e}）")


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_extra()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す1回）を、1万回の中から選ぶ
# =====================================================================
COLS, ROWS = 125, 80                                 # 町の家々（1軒＝1人）。125×80＝1万軒
_SAMPLE = {}


def samples():
    """見本の1回: 1万回のうち「聞いた人の数が 中央値に（±5人で）近く」「町の半分に届く日数も 中央値に いちばん近い」1回。
    1万回の中の1回そのもの（同じ乱数で 人ごとの記録を取り直す）"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    m = r["main"]
    med = float(np.median(m["heard"]))
    pool = np.nonzero(np.abs(m["heard"] - med) <= 5)[0]
    th_med = float(np.nanmedian(m["t_half"]))
    h = int(pool[np.argmin(np.abs(m["t_half"][pool] - th_med))])
    rec = run_single(SEED_MAIN, h, C_BASE, N_TOWN, track=True)
    th, ts = rec["th"], rec["ts"]
    ev = np.sort(np.concatenate([th[1:], ts[np.isfinite(ts)]]))
    rng = np.random.default_rng(777)
    center = (ROWS // 2) * COLS + COLS // 2
    others = rng.permutation(np.delete(np.arange(COLS * ROWS), center))
    pos = np.concatenate([[center], others])         # 聞いた順の番号 → 家（セル）の番号
    _SAMPLE.update(h=h, rec=rec, th=th, ts=ts, ev=ev, pos=pos, med=med, th_med=th_med)
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    S = samples()
    rec = S["rec"]
    print(f"見本: 回 #{S['h']}  聞いた人 {rec['heard']}人（1万回の中央値 {S['med']:.0f}人）  聞かなかった {N_TOWN - rec['heard']}人  "
          f"半分に届く {rec['t_half']:.2f}日（中央値 {S['th_med']:.2f}日）  止まるまで {rec['t_end']:.2f}日  歩数 {rec['steps']}")
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
note.DATE = "11.16"                                  # 日付欄（公開予定日）

C_IGN, C_IGN_D = "#c3c7cd", "#9aa0ab"                # 知らない人（灰色）
C_SPR, C_SPR_D = "#ffd23a", "#e29d00"                # 話している人（黄色）
C_STP, C_STP_D = "#3b7ddd", "#2757a8"                # もう話さない人（青）
C_ROAD = "#e9e1cc"
BAR = "#3f7fb5"
SKIN = "#f4d2b5"

# 記号の並び・正解は ここ（と comment.txt）だけ。正解の記号は A（1番目）
LABELS = ["約8割", "約9割", "ほぼ全員"]
KEY_LABEL = {"eight": "約8割", "nine": "約9割", "all": "ほぼ全員"}
CORRECT = 0                                         # answer_by_rule の結果の位置（A）

BIG_Q3 = ["1万人の町で、", "うわさは何割の人に", "届く？"]                  # 1コマ目の3行（同じ大きさ）
BIG_Q = ["1万人の町で、", "うわさは何割の人に届く？"]                       # 定位置（上）の2行
DETAIL_RULE = "聞いた人は 町の何割？（1人から始めて1日に5人と話す）"
DETAIL = "うわさをもう知っている人に会うと、話すのをやめる（計算での見立て）"
SPEECH_A = ["駅前に新しいパン屋が", "できるらしいよ"]
SPEECH_B = ["えっ、そうなの？"]

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_X, CARD_W, CARD_H = 100.0, 910.0, 670.0
CARD_Y_INTRO, CARD_Y_FINAL = 840.0, 600.0
CD_X, CD_Y = 790.0, 970.0
MAP_X0, MAP_Y0 = 18.0, 58.0                          # カード内の 町の図の左上
CS, RD, GAPPX, ROOF = 6.8, 6.0, 1.0, 2.2            # 1軒の幅・道の幅・軒の間のすき間・屋根の高さ（px）
T_BUB_A, T_BUB_B = 0.4, 2.0                          # 吹き出しが出る時刻


def setup():
    global T_MAP, T_RUN0, T_RUN_HOLD, T_RUN1, T_D0, T_D1, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TS1, T_TW2, T_Q, DURATION, SCENES
    T_MAP = T_GO + 3.6                              # 立ち話 → 町を上から見た図
    T_RUN0 = T_MAP + 0.6                            # 町の図が見える
    T_RUN_HOLD = 0.9                                # 最初の1人だけ（見つける時間）
    T_RUN1 = T_RUN0 + T_RUN_HOLD + 6.2              # 見本の1回が止まる
    T_D0 = T_RUN1 + 3.2                             # 1万回の結果の山へ
    T_D1 = T_D0 + 0.8 + 2.4                         # 山が積み終わる
    T_DN = T_D1 + 0.1                               # 数字1（中央値）
    T_DN2 = T_DN + 2.8                              # 数字2（止まった回・全員に届いた回）
    T_REV = T_DN2 + 3.0                             # 答え
    T_ANS2 = T_REV + 2.6                            # 理由
    T_TW = T_ANS2 + 3.2                             # ひねり
    T_TS1 = T_TW + 0.8 + 1.6                        # 棒が伸び終わる
    T_TW2 = T_TW + 3.6                              # ひねりの答え
    T_Q = T_TW2 + 3.6                               # 締め
    DURATION = T_Q + 4.2
    SCENES = [("立ち話（最初の1人）", T_GO, T_MAP), ("見本の1回（町を上から見た図）", T_MAP, T_D0),
              ("1万回の結果（答え・理由）", T_D0, T_TW), ("ひねり（1日に会う人数別）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def p1(x):
    """割合 → 小数1桁の%（0.7968 → '79.7%'）"""
    return f"{math.floor(x * 1000 + 0.5) / 10:.1f}%"


def oku_text(p):
    """確率 p → 「約N回に1回」。大きい数は 億・万 で言う"""
    v = 1.0 / p
    for unit, nm in ((1e8, "億"), (1e4, "万")):
        if v >= 0.95 * unit:
            return f"約{int(round(v / unit))}{nm}回に1回"
    return f"約{int(round(v))}回に1回"


def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def thick(ctx, pts, w, col, outline=2.4):
    """太い線（ふちどり付き）"""
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    for ww, cc, aa in ((w + 2 * outline, INK, 0.9), (w, col, 1.0)):
        for i, (x, y) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(x, y)
        ctx.set_source_rgba(*hexrgb(cc, aa))
        ctx.set_line_width(ww)
        ctx.stroke()


# ---------- 絵: 人（正面・頭は内側を向く） ----------
PERSON_A = dict(girl=True, hair="#4a3224", style="long", top="#e8b53a", top_d="#c4912a", inner="#fbf6ea",
                bottom="#3d6b78", shoe="#6b4a3a", ph=0.0)
PERSON_B = dict(girl=False, hair="#2a2a31", style="short", top="#4f9a6a", top_d="#3b7a52", inner="#f3efe6",
                bottom="#4a5f8f", shoe="#ece7dd", ph=1.7)
PERSON_C = dict(girl=True, hair="#7a4a2a", style="bob", top="#d9697a", top_d="#b24e5f", inner="#fbf6ea",
                bottom="#5b5f82", shoe="#3b3636", ph=3.1)


def person(ctx, x, fy, k, st, look, t, talk=0.0, arm=0.0, blink_ph=0.0):
    """正面向きの人。(x, fy) は足もとの中心、身長は およそ 104·k px。look=+1 なら右、−1 なら左（内側）を見る。
    talk=口の開き（0〜1）。arm=右（look 側）の手を上げる度合い（0〜1。身ぶり）"""
    hs = look if look else 1
    b = 0.45 * math.sin(t * 2.3 + st["ph"])                           # 息づかい（上半身の上下）
    P = lambda dx, dy: (x + dx * k, fy + dy * k)                    # noqa: E731
    PU = lambda dx, dy: (x + dx * k, fy + (dy + b) * k)             # noqa: E731  上半身
    lw = max(2.2, 0.7 * k)
    ctx.save()
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def poly(pts, col, w=None, upper=True):
        ctx.new_path()
        for i, (px, py) in enumerate(pts):
            (ctx.move_to if i == 0 else ctx.line_to)(*(PU if upper else P)(px, py))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, w or lw, INK, 0.9)

    if st["style"] == "long":                                        # 長い髪（うしろ）
        ctx.new_path()
        ctx.move_to(*PU(-10.2, -94))
        ctx.curve_to(*PU(-15, -84), *PU(-14.5, -70), *PU(-11.5, -63))
        ctx.line_to(*PU(11.5, -63))
        ctx.curve_to(*PU(14.5, -70), *PU(15, -84), *PU(10.2, -94))
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(st["hair"]))
        ctx.fill_preserve()
        _stroke(ctx, lw, INK, 0.9)
    # 脚・くつ
    for dx in (-6.6, 6.6):
        if st["girl"]:
            thick(ctx, [P(dx, -32), P(dx, -7)], 7.2 * k, SKIN, 2.1)
            thick(ctx, [P(dx, -13), P(dx, -6.8)], 7.8 * k, "#fbf6ea", 2.1)
        else:
            thick(ctx, [P(dx, -46), P(dx, -6)], 12.6 * k, st["bottom"], 2.3)
        sx, sy = P(dx + look * 1.5, -2.7)
        ctx.save()
        ctx.translate(sx, sy)
        ctx.scale(1.0, 0.52)
        ctx.arc(0, 0, 6.7 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb(st["shoe"]))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.9, INK, 0.9)
    if st["girl"]:                                                   # スカート
        poly([(-14.6, -48), (14.6, -48), (19.5, -26), (-19.5, -26)], st["bottom"], lw, upper=False)
        for dx in (-9, -3, 3, 9):
            ctx.move_to(*P(dx * 0.8, -47))
            ctx.line_to(*P(dx * 1.25, -26.5))
            _stroke(ctx, lw * 0.5, INK, 0.3)
    # 手を出さないほうのうで
    sx0, sy0 = PU(-hs * 16.0, -77.0)
    thick(ctx, [(sx0, sy0), PU(-hs * 19.5, -64), PU(-hs * 19.0, -51.5)], 7.4 * k, st["top"], 2.3)
    ctx.new_path()
    ctx.arc(*PU(-hs * 19.3, -47.5), 3.9 * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    # 上着（カーディガン／ジャケット）
    ctx.new_path()
    ctx.move_to(*PU(-8.5, -83))
    ctx.curve_to(*PU(-14, -82), *PU(-18.5, -80.5), *PU(-18.3, -73))
    ctx.line_to(*PU(-15.2, -44))
    ctx.line_to(*PU(15.2, -44))
    ctx.line_to(*PU(18.3, -73))
    ctx.curve_to(*PU(18.5, -80.5), *PU(14, -82), *PU(8.5, -83))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(st["top"]))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    poly([(-5.2, -83), (0, -68), (5.2, -83)], st["inner"], lw * 0.8)    # 中に着たシャツ
    ctx.move_to(*PU(0, -68))
    ctx.line_to(*PU(0, -44))
    _stroke(ctx, lw * 0.9, INK, 0.7)
    poly([(-5.2, -83), (-9.4, -71), (-3.4, -63.5), (0, -68)], st["top_d"], lw * 0.8)    # 襟
    poly([(5.2, -83), (9.4, -71), (3.4, -63.5), (0, -68)], st["top_d"], lw * 0.8)
    for by_ in (-58.0, -51.0):                                       # ボタン
        ctx.new_path()
        ctx.arc(*PU(3.0 if hs > 0 else -3.0, by_), 0.9 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(st["top_d"]))
        ctx.fill()
    # 身ぶりの手（look 側）
    shx, shy = PU(hs * 15.8, -77.0)
    wr = (hs * (18.6 + 3.0 * arm), -49.0 - 37.0 * arm)
    el = (hs * (20.2 + 8.0 * arm), -63.5 - 4.0 * arm)
    thick(ctx, [(shx, shy), PU(*el), PU(*wr)], 7.4 * k, st["top"], 2.3)
    hx_, hy_ = PU(wr[0] + hs * 0.6, wr[1] - 3.6 * arm - 1.0)
    ctx.new_path()
    ctx.arc(hx_, hy_, (3.9 + 0.9 * arm) * k, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    # 首・頭
    core.rrect(ctx, *PU(-3.4, -84), 6.8 * k, 6.5 * k, 2 * k)
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw * 0.9, INK, 0.9)
    ctx.save()
    nx, ny = PU(0, -82)
    ctx.translate(nx, ny)
    ctx.rotate(look * 0.06)
    ctx.translate(-nx, -ny)
    for sg in (-1, 1):                                               # 耳
        ctx.new_path()
        ctx.arc(*PU(sg * 9.0, -92), 2.2 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(SKIN))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.save()                                                       # 顔
    ctx.translate(*PU(0, -92.5))
    ctx.scale(1.0, 1.08)
    ctx.arc(0, 0, 9.1 * k, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(SKIN))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    hair = st["hair"]                                                # 髪
    ctx.new_path()
    ctx.move_to(*PU(-9.7, -91))
    ctx.curve_to(*PU(-11.8, -107.5), *PU(11.8, -107.5), *PU(9.7, -91))
    ctx.line_to(*PU(9.0, -97))
    ctx.line_to(*PU(6.0, -98.8))
    ctx.line_to(*PU(2.2, -96.6))
    ctx.line_to(*PU(-1.8, -98.8))
    ctx.line_to(*PU(-5.4, -96.6))
    ctx.line_to(*PU(-8.6, -98.2))
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(hair))
    ctx.fill_preserve()
    _stroke(ctx, lw, INK, 0.92)
    if st["style"] in ("bob", "long"):
        ln = 13.0 if st["style"] == "bob" else 15.5
        for sg in (-1, 1):
            core.rrect(ctx, *PU(sg * 10.4 - 2.1, -99), 4.2 * k, ln * k, 2.0 * k)
            ctx.set_source_rgba(*hexrgb(hair))
            ctx.fill_preserve()
            _stroke(ctx, lw * 0.9, INK, 0.9)
    blink = ((t * 0.9 + blink_ph + st["ph"] * 0.3) % 3.4) < 0.12
    for sg in (-1, 1):                                               # 目・まゆ・ほお
        ex, ey = PU(sg * 3.6 + look * 1.5, -92.2)
        if blink:
            ctx.move_to(ex - 1.8 * k, ey)
            ctx.line_to(ex + 1.8 * k, ey)
            _stroke(ctx, lw * 0.9, INK, 0.95)
        else:
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(0.78, 1.0)
            ctx.arc(0, 0, 1.95 * k, 0, 2 * math.pi)
            ctx.restore()
            ctx.set_source_rgba(*hexrgb(INK))
            ctx.fill()
            ctx.new_path()
            ctx.arc(ex + look * 0.5 * k + 0.45 * k, ey - 0.55 * k, 0.55 * k, 0, 2 * math.pi)
            ctx.set_source_rgba(1, 1, 1, 0.95)
            ctx.fill()
        bx, by = PU(sg * 3.7 + look * 1.5, -95.4)
        ctx.move_to(bx - 2.0 * k, by + 0.25 * k)
        ctx.line_to(bx + 2.0 * k, by - 0.25 * k)
        _stroke(ctx, lw * 0.8, INK, 0.8)
        ctx.new_path()
        ctx.arc(*PU(sg * 6.1 + look * 1.2, -89.0), 1.5 * k, 0, 2 * math.pi)
        ctx.set_source_rgba(1.0, 0.55, 0.55, 0.32)
        ctx.fill()
    mx_, my_ = PU(look * 1.3, -87.2)                                 # 口
    if talk > 0.05:
        ctx.save()
        ctx.translate(mx_, my_)
        ctx.scale(1.0, 0.5 + 0.9 * talk)
        ctx.arc(0, 0, 1.8 * k, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#b5434b"))
        ctx.fill_preserve()
        _stroke(ctx, lw * 0.7, INK, 0.9)
    else:
        ctx.new_path()
        ctx.arc(mx_, my_ - 0.4 * k, 2.3 * k, 0.2 * math.pi, 0.8 * math.pi)
        _stroke(ctx, lw * 0.8, INK, 0.9)
    ctx.restore()
    ctx.restore()


# ---------- 絵: 町の通り（立ち話の背景） ----------

def house_side(ctx, x, gy, w, h, wall, roof, door="#8a5a3a"):
    """横から見た家。(x, gy) は 左下の地面"""
    ctx.rectangle(x, gy - h, w, h)
    ctx.set_source_rgba(*hexrgb(wall))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.75)
    ctx.move_to(x - 10, gy - h)
    ctx.line_to(x + w / 2, gy - h - 0.55 * w)
    ctx.line_to(x + w + 10, gy - h)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(roof))
    ctx.fill_preserve()
    _stroke(ctx, 3, INK, 0.75)
    for wx in (x + 0.14 * w, x + 0.62 * w):
        rrect(ctx, wx, gy - h + 0.2 * h, 0.24 * w, 0.28 * h, 4)
        ctx.set_source_rgba(*hexrgb("#d7ecf7"))
        ctx.fill_preserve()
        _stroke(ctx, 2.5, INK, 0.7)
    rrect(ctx, x + 0.42 * w, gy - 0.4 * h, 0.17 * w, 0.4 * h, 4)
    ctx.set_source_rgba(*hexrgb(door))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.7)


def tree(ctx, x, gy, s):
    rrect(ctx, x - 7 * s, gy - 70 * s, 14 * s, 72 * s, 4)
    ctx.set_source_rgba(*hexrgb("#8a5a3a"))
    ctx.fill_preserve()
    _stroke(ctx, 2.5, INK, 0.7)
    for dx, dy, r in ((0, -95, 38), (-26, -74, 28), (26, -74, 28)):
        ctx.arc(x + dx * s, gy + dy * s, r * s, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb("#7fbf7a"))
        ctx.fill_preserve()
        _stroke(ctx, 2.5, INK, 0.7)


def draw_street_bg(ctx, w, h, gy):
    """通りの背景。w×h の中に 空・家々・歩道・道路。gy は 人が立つ地面の y"""
    g = cairo.LinearGradient(0, 0, 0, gy)
    g.add_color_stop_rgb(0, *hexrgb("#bfe3f5")[:3])
    g.add_color_stop_rgb(1, *hexrgb("#eef8fb")[:3])
    ctx.set_source(g)
    ctx.rectangle(0, 0, w, gy)
    ctx.fill()
    base = gy - 70
    house_side(ctx, 40, base, 190, 130, "#f2d9b8", "#c8645a")
    house_side(ctx, 270, base, 150, 105, "#d9e8c8", "#6c8fb8", "#9a6a46")
    house_side(ctx, w - 270, base, 200, 140, "#f6e7a8", "#8a6fb0")
    tree(ctx, w - 40, base + 8, 1.0)
    tree(ctx, 455, base + 8, 0.8)
    ctx.rectangle(0, base, w, gy - base + 10)                               # 歩道
    ctx.set_source_rgba(*hexrgb("#d9d2c2"))
    ctx.fill()
    ctx.move_to(0, base)
    ctx.line_to(w, base)
    _stroke(ctx, 3, INK, 0.5)
    ctx.rectangle(0, gy + 10, w, h - gy)                                    # 道路
    ctx.set_source_rgba(*hexrgb("#8d939c"))
    ctx.fill()
    for i in range(0, int(w), 120):
        rrect(ctx, i + 20, gy + 70, 70, 10, 4)
        ctx.set_source_rgba(1, 1, 1, 0.75)
        ctx.fill()


def bubble(ctx, lines, x0, y0, bw, bh, tail_to, a=1.0, size=34, pop=1.0, side="bottom"):
    """吹き出し（白・黒い縁）。tail_to = しっぽの先 (x, y)"""
    if a <= 0:
        return
    ctx.save()
    cx, cy = x0 + bw / 2, y0 + bh / 2
    ctx.translate(cx, cy)
    ctx.scale(pop, pop)
    ctx.translate(-cx, -cy)
    ctx.push_group()
    rrect(ctx, x0, y0, bw, bh, 26)
    ctx.set_source_rgba(1, 1, 1, 0.98)
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    tx, ty = tail_to
    if side == "left":
        ctx.move_to(x0 + 2, cy - 12)
        ctx.line_to(tx, ty)
        ctx.line_to(x0 + 2, cy + 14)
        ctx.set_source_rgba(1, 1, 1, 0.98)
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
        rrect(ctx, x0 - 2, cy - 11, 10, 24, 3)
        ctx.set_source_rgba(1, 1, 1, 0.99)
        ctx.fill()
    else:
        bx = min(max(tx, x0 + 40), x0 + bw - 40)
        ctx.move_to(bx - 20, y0 + bh - 2)
        ctx.line_to(tx, ty)
        ctx.line_to(bx + 22, y0 + bh - 2)
        ctx.set_source_rgba(1, 1, 1, 0.98)
        ctx.fill_preserve()
        _stroke(ctx, 3.5, INK, 0.9)
        rrect(ctx, bx - 21, y0 + bh - 8, 44, 10, 3)
        ctx.set_source_rgba(1, 1, 1, 0.99)
        ctx.fill()
    text(ctx, "\n".join(lines), cx, cy + 2, size, INK, bold=False)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


# 立ち話の絵（カード内の座標）
ST_AX, ST_BX, ST_FY, ST_K = 250.0, 520.0, 612.0, 3.9
ST_GY = ST_FY + 4.0


def draw_street(ctx, t, w, h):
    draw_street_bg(ctx, w, h, ST_GY)
    # 話している間（A が話す・B が答える）。口と身ぶりを時間で動かす
    a_on = T_BUB_A <= t < T_BUB_B + 0.2 or t >= T_BUB_B + 1.9
    b_on = T_BUB_B <= t < T_BUB_B + 1.9
    a_talk = 0.5 + 0.5 * math.sin(t * 9.0) if a_on else 0.0
    b_talk = 0.5 + 0.5 * math.sin(t * 9.0 + 1.0) if b_on else 0.0
    ga = 0.5 + 0.5 * math.sin(t * 3.1)
    person(ctx, ST_AX, ST_FY, ST_K, PERSON_A, 1, t, talk=a_talk if a_talk > 0.35 else 0.0, arm=0.55 * ga if a_on else 0.0)
    person(ctx, ST_BX, ST_FY, ST_K, PERSON_B, -1, t, talk=b_talk if b_talk > 0.35 else 0.0, arm=0.0, blink_ph=1.1)
    sa = ease_out((t - T_BUB_A) / 0.3)
    sb = ease_out((t - T_BUB_B) / 0.3)
    bubble(ctx, SPEECH_A, 70, 30, 410, 130, (ST_AX + 36, ST_FY - 108 * ST_K - 2), a=sa, pop=0.85 + 0.15 * sa)
    bubble(ctx, SPEECH_B, 578, 232, 245, 76, (ST_BX + 40, ST_FY - 94 * ST_K), a=sb, pop=0.85 + 0.15 * sb, size=30, side="left")


# ---------- 絵: 町の家々（上から見た図） ----------
_MAPG = {}


def map_geometry():
    if _MAPG:
        return _MAPG
    col_start = np.array([c * CS + RD * (c // 25) for c in range(COLS)])
    row_start = np.array([r * CS + RD * (r // 20) for r in range(ROWS)])
    mw = int(math.ceil(col_start[-1] + CS))
    mh = int(math.ceil(row_start[-1] + CS))
    xs = np.arange(mw) + 0.5
    ys = np.arange(mh) + 0.5
    ci = np.clip(np.searchsorted(col_start, xs, "right") - 1, 0, COLS - 1)
    ri = np.clip(np.searchsorted(row_start, ys, "right") - 1, 0, ROWS - 1)
    vx = (xs - col_start[ci]) < (CS - GAPPX)
    vy = (ys - row_start[ri]) < (CS - GAPPX)
    roof = ((ys - row_start[ri]) < ROOF)[:, None] & np.ones(mw, bool)[None, :]
    valid = vy[:, None] & vx[None, :]
    pal = np.zeros((7, 4), np.uint8)
    for i, c in enumerate((C_IGN, C_SPR, C_STP, C_IGN_D, C_SPR_D, C_STP_D, C_ROAD)):
        r_, g_, b_, _a = hexrgb(c)
        pal[i] = (int(b_ * 255), int(g_ * 255), int(r_ * 255), 255)
    _MAPG.update(mw=mw, mh=mh, ci=ci, ri=ri, valid=valid, roof=roof, pal=pal)
    return _MAPG


def map_surface(cellstate):
    """町の図: 1軒＝1人。cellstate（ROWS×COLS の 0知らない/1話している/2もう話さない）→ 画像"""
    g = map_geometry()
    st = cellstate[g["ri"][:, None], g["ci"][None, :]].astype(np.int16)
    code = np.where(g["valid"], st + 3 * g["roof"], 6)
    buf = np.ascontiguousarray(g["pal"][code])
    surf = cairo.ImageSurface.create_for_data(memoryview(buf), cairo.FORMAT_ARGB32, g["mw"], g["mh"], g["mw"] * 4)
    return surf, buf


def run_progress(t):
    """動画の時刻 → 見本の1回の 進み（0〜1）。出来事（聞いた・やめた）の数に そろえて進める"""
    return clamp01((t - T_RUN0 - T_RUN_HOLD) / (T_RUN1 - T_RUN0 - T_RUN_HOLD))


def run_state(t):
    S = samples()
    th, ts, ev, pos = S["th"], S["ts"], S["ev"], S["pos"]
    u = run_progress(t)
    k = int(len(ev) * u)
    tau = float(ev[min(k, len(ev)) - 1]) if k > 0 else 0.0
    n = int(np.searchsorted(th, tau, "right"))
    stopped = ts[:n] <= tau
    cell = np.zeros(COLS * ROWS, np.uint8)
    cell[pos[:n]] = 1 + stopped.astype(np.uint8)
    n_stop = int(stopped.sum())
    return dict(tau=tau, n=n, n_stop=n_stop, n_spread=n - n_stop, cell=cell.reshape(ROWS, COLS), done=u >= 1.0)


def map_xy(order_idx):
    """聞いた順 order_idx の人の家の 中心（カード内の px）"""
    S = samples()
    c = int(S["pos"][order_idx])
    r_, c_ = divmod(c, COLS)
    return (MAP_X0 + c_ * CS + RD * (c_ // 25) + (CS - GAPPX) / 2, MAP_Y0 + r_ * CS + RD * (r_ // 20) + (CS - GAPPX) / 2)


def legend_row(ctx, y, size=28, x_left=34.0):
    items = ((C_IGN, "知らない人"), (C_SPR, "話している人"), (C_STP, "もう話さない人"))
    x = x_left
    for col, lab in items:
        rrect(ctx, x, y - 13, 26, 26, 5)
        ctx.set_source_rgba(*hexrgb(col))
        ctx.fill_preserve()
        _stroke(ctx, 2.2, INK, 0.8)
        text(ctx, lab, x + 36, y, size, INK, align="left", bold=False)
        x += 36 + core.text_width(lab, size, False) + 40


def draw_map(ctx, t, a):
    """カード内の町の図（a=不透明度）"""
    if a <= 0:
        return
    rs = run_state(t)
    ctx.save()
    ctx.translate(MAP_X0, MAP_Y0)
    surf, _keep = map_surface(rs["cell"])
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(a)
    ctx.restore()
    text(ctx, "1万軒の町を上から見た図（1軒に1人）", 34, 30, 28, INK, align="left", alpha=a)
    text(ctx, "計算での見立て", 880, 30, 24, PENCIL, align="right", bold=False, alpha=a)
    legend_row(ctx, CARD_H - 30)
    # 最初の1人の目印
    if t < T_RUN0 + T_RUN_HOLD + 1.2:
        q = ease_out((t - T_RUN0) / 0.3) * (1 - ease((t - T_RUN0 - T_RUN_HOLD - 0.5) / 0.7)) * a
        if q > 0:
            x0, y0 = map_xy(0)
            x0, y0 = x0 + MAP_X0, y0 + MAP_Y0 - 0.0
            note.pen_circle(ctx, x0, y0, 20, 20, RED, seed=9, width=5, progress=clamp01((t - T_RUN0) / 0.4), alpha=q)
            rrect(ctx, x0 + 36, y0 - 70, 262, 44, 10)
            ctx.set_source_rgba(*hexrgb(PAPER, 0.96 * q))
            ctx.fill()
            text(ctx, "最初に知っている1人", x0 + 167, y0 - 48, 28, RED, alpha=q)


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, CARD_H, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    ctx.clip()
    am = ease((t - T_MAP) / 0.6)
    if am < 1.0:
        draw_street(ctx, t, CARD_W, CARD_H)
    if am > 0:
        ctx.push_group()
        fill(ctx, "#f2eddc")
        ctx.paint()
        draw_map(ctx, t, 1.0)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(am)
    ctx.restore()
    rrect(ctx, 12, 12, CARD_W - 24, CARD_H - 24, 14)
    _stroke(ctx, 3.2, INK, 0.85)
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
    S = samples()
    if T_GO + 0.2 <= t < T_MAP + 0.3:                                       # 立ち話のあいだ
        s_ = ease_out((t - T_GO - 0.2) / 0.25) * (1 - ease((t - T_MAP - 0.05) / 0.25))
        note.sticky(ctx, "最初に知っているのは\nたった1人（1万人の町）", 590, 1368, 38, "yellow", a=s_, tilt=-0.02)
    if T_RUN0 <= t < T_RUN1 + 0.1:                                          # 数え（カードの下）
        rs = run_state(t)
        s_ = ease_out((t - T_RUN0 - 0.2) / 0.25)
        note.sticky(ctx, f"{rs['tau']:.1f}日後\n聞いた人 {fmt(rs['n'])}人\n話している人 {fmt(rs['n_spread'])}人", 590, 1366, 34,
                    "mint", a=s_ * (1 - ease((t - T_RUN1) / 0.1)), tilt=0.02)
    if t >= T_RUN1:
        s_ = ease_out((t - T_RUN1) / 0.25) * (1 - ease((t - T_D0) / 0.25))
        un = N_TOWN - S["rec"]["heard"]
        note.sticky(ctx, f"たとえば、この1回では\n聞かなかった人は {fmt(un)}人\n（町の {pct(un / N_TOWN)}%）", 590, 1366, 34, "yellow", a=s_,
                    tilt=0.02)


# ---------- 1万回の結果（聞いた人の割合の山） ----------
FR_X0, FR_X1, FR_Y0, FR_Y1 = 100.0, 1010.0, 600.0, 1215.0
H_LO, H_BIN, H_NB = 0.770, 0.001, 50                  # 山の横軸: 77%〜82%・0.1%きざみ
HX0, HPX = 130.0, 144.0                              # 77% の x と 1%あたりの px
H_BASE, H_HEIGHT = 1065.0, 300.0
_HIST = {}


def hist_data():
    if not _HIST:
        r = results()
        f = r["f"]
        b = np.clip(((f - H_LO) / H_BIN).astype(int), 0, H_NB - 1)
        cum = np.zeros((N_RUN // 100 + 1, H_NB), np.int32)
        for i in range(1, N_RUN // 100 + 1):
            cum[i] = np.bincount(b[:i * 100], minlength=H_NB)
        _HIST.update(cum=cum, peak=int(np.bincount(b, minlength=H_NB).max()))
    return _HIST


def hx(frac):
    return HX0 + (frac * 100 - H_LO * 100) * HPX


def frame_box(ctx, a):
    rrect(ctx, FR_X0, FR_Y0, FR_X1 - FR_X0, FR_Y1 - FR_Y0, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97 * a))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75 * a)


def hist_alpha(t):
    if t < T_D0:
        return 0.0
    return ease((t - T_D0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    st = unheard_stats(r["main"])
    hd = hist_data()
    frame_box(ctx, a)
    pr = clamp01((t - T_D0 - 0.8) / (T_D1 - T_D0 - 0.8))
    m_rev = N_RUN if pr >= 1 else int(N_RUN * ease(pr))
    text(ctx, "1万回やってみた結果（聞いた人の割合）", 555, 642, 34, INK, alpha=a)
    text(ctx, f"町の1人から流す1回を {fmt(m_rev)} / 10,000 回ためした", 555, 686, 26, PENCIL, bold=False, alpha=a)
    ctx.move_to(HX0 - 20, H_BASE)
    ctx.line_to(HX0 + 5.0 * HPX + 20, H_BASE)
    _stroke(ctx, 3, INK, 0.75 * a)
    cnt = hd["cum"][min(m_rev // 100, N_RUN // 100)]
    for i in range(H_NB):
        hgt = H_HEIGHT * cnt[i] / hd["peak"]
        if hgt < 0.5:
            continue
        x = HX0 + i * H_BIN * 100 * HPX
        ctx.rectangle(x + 1, H_BASE - hgt, H_BIN * 100 * HPX - 2, hgt)
        ctx.set_source_rgba(*hexrgb(BAR, 0.92 * a))
        ctx.fill()
    for v in range(77, 83):
        x = HX0 + (v - 77) * HPX
        ctx.move_to(x, H_BASE)
        ctx.line_to(x, H_BASE + 10)
        _stroke(ctx, 2.5, INK, 0.7 * a)
        text(ctx, f"{v}%", x, H_BASE + 36, 28, INK, bold=False, alpha=a)
    if pr >= 1.0 or t >= T_D1:                                              # 中央値の線・いちばん届いた回/届かなかった回
        u = ease_out((t - T_D1 + 0.3) / 0.4) * a
        xm = hx(r["m"])
        ctx.set_dash([10, 7])
        ctx.move_to(xm, H_BASE + 2)
        ctx.line_to(xm, H_BASE - H_HEIGHT - 14)
        _stroke(ctx, 3.5, RED, 0.9 * u)
        ctx.set_dash([])
        text(ctx, "中央値", xm, H_BASE - H_HEIGHT - 32, 28, RED, alpha=u)
        for fv, nm in ((st["lo"], "いちばん届かなかった回"), (st["hi"], "いちばん届いた回")):
            x = hx(fv)
            ctx.move_to(x, H_BASE + 54)
            ctx.line_to(x - 10, H_BASE + 76)
            ctx.line_to(x + 10, H_BASE + 76)
            ctx.close_path()
            ctx.set_source_rgba(*hexrgb(INK, 0.55 * u))
            ctx.fill()
            xx = min(x, 805.0) if fv == st["hi"] else max(x, 255.0)
            text(ctx, f"{nm}\n{p1(fv)}", xx, H_BASE + 116, 26, INK, bold=False, alpha=u)
    if t >= T_DN:                                                           # 数字1: 中央値
        u = ease_out((t - T_DN) / 0.3) * a
        cx2 = 800.0
        text(ctx, "聞いた人の割合", cx2, 742, 30, INK, bold=False, alpha=u)
        text(ctx, p1(r["m"]), cx2, 806, 84, RED, alpha=u)
        text(ctx, "中央値（1万回の\nちょうど真ん中の値）", cx2, 880, 26, PENCIL, bold=False, alpha=u)
    if t >= T_DN2:                                                          # 数字2: 止まった回・全員に届いた回
        u = ease_out((t - T_DN2) / 0.3) * a
        cx3 = 285.0
        text(ctx, "最初の数人で止まった回", cx3, 742, 26, INK, bold=False, alpha=u)
        text(ctx, f"{st['early']}回", cx3, 790, 54, RED, alpha=u)
        text(ctx, "全員（99%以上）に届いた回", cx3, 846, 26, INK, bold=False, alpha=u)
        text(ctx, f"{st['full']}回", cx3, 894, 54, RED, alpha=u)


# ---------- 答え・理由 ----------

def answer_key():
    return answer_by_rule(results()["m"])


def reason_text():
    return "話す人は、うわさをもう知っている人に\n会うと、話すのをやめる。\nだから、全員に届く前にうわさが止まる。"


TW_Q = "では、毎日もっと\n多くの人と話すと？"


def tw_a():
    return "話す人数を増やすと、うわさは速く広がる。\nそれでも、聞かない人は約2割のまま。"


def tw_b():
    r = results()
    ds = [unheard_stats(r["by_c"][c])["half_days"] for c in C_SHOW]
    return f"（町の半分に届くまで {ds[0]:.1f}日 → {ds[1]:.1f}日 → {ds[2]:.1f}日）"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"答えは『{KEY_LABEL[key]}』。", 590, 1258, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 590, 1372, 26, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 590, 1258, 38, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        for k_, ln_ in enumerate(tw_a().split("\n")):
            text(ctx, ln_, 570, 1360 + 40 * k_, 34, RED, alpha=e)
        text(ctx, tw_b(), 555, 1436, 26, INK, bold=False, alpha=e)


# ---------- ひねり（1日に会う人数別） ----------

def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


TW_BASE, TW_HB = 1100.0, 280.0
TWA_X = (185.0, 300.0, 415.0)
TWB_X = (610.0, 740.0, 870.0)


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    r = results()
    frame_box(ctx, a)
    text(ctx, "1日に話す人数を変えて、1万回ずつ", 555, 642, 34, INK, alpha=a)
    text(ctx, "町の半分に届くまでの日数", 300, 718, 28, INK, alpha=a)
    text(ctx, "最後まで聞かなかった人の割合", 740, 718, 28, INK, alpha=a)
    text(ctx, "（中央値）", 300, 756, 26, PENCIL, bold=False, alpha=a)
    text(ctx, "（中央値）", 740, 756, 26, PENCIL, bold=False, alpha=a)
    for base_x in (TWA_X, TWB_X):
        ctx.move_to(base_x[0] - 70, TW_BASE)
        ctx.line_to(base_x[2] + 70, TW_BASE)
        _stroke(ctx, 3, INK, 0.7 * a)
    pr = ease(clamp01((t - T_TW - 0.8) / (T_TS1 - T_TW - 0.8)))
    ds = [unheard_stats(r["by_c"][c]) for c in C_SHOW]
    dmax = max(d["half_days"] for d in ds)
    for i, c in enumerate(C_SHOW):
        hg = TW_HB * ds[i]["half_days"] / dmax * pr
        rrect(ctx, TWA_X[i] - 40, TW_BASE - hg, 80, max(hg, 1.0), 8)
        ctx.set_source_rgba(*hexrgb(BAR, 0.9 * a))
        ctx.fill()
        text(ctx, f"{ds[i]['half_days'] * pr:.1f}日", TWA_X[i], TW_BASE - hg - 28, 36, RED, alpha=a)
        text(ctx, f"{c}人", TWA_X[i], TW_BASE + 36, 34, INK, alpha=a)
        un = 1 - ds[i]["med"]
        hg2 = TW_HB * (un / 0.25) * pr
        rrect(ctx, TWB_X[i] - 40, TW_BASE - hg2, 80, max(hg2, 1.0), 8)
        ctx.set_source_rgba(*hexrgb("#d98a4a", 0.9 * a))
        ctx.fill()
        text(ctx, p1(un * pr), TWB_X[i], TW_BASE - hg2 - 28, 34, RED, alpha=a)
        text(ctx, f"{c}人", TWB_X[i], TW_BASE + 36, 34, INK, alpha=a)


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
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・前提・三択（横1列）。その下に町の通りの立ち話（0秒目から動き、場面が寄った所から引く）"""
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


# ---------- 締め（立ち話の2人） ----------

def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "あなたが最後に聞いたうわさは、\nだれから聞きましたか？", 580, 800, 50, "yellow", a=q, tilt=-0.02)
    r = ease_out((t - T_Q - 0.9) / 0.3)
    text(ctx, "コメントで教えてください", 580, 972, 36, INK, bold=False, alpha=r)
    ctx.save()
    ctx.push_group()
    rrect(ctx, 150, 1050, 820, 380, 24)
    ctx.clip()
    ctx.translate(150, 1050)
    draw_street_bg(ctx, 820, 380, 345.0)
    tt = t - T_Q
    ph = math.sin(tt * 9.0)
    person(ctx, 270, 350.0, 3.05, PERSON_C, 1, t, talk=0.8 if ph > 0.2 else 0.0, arm=0.5 + 0.5 * math.sin(tt * 3.0))
    person(ctx, 520, 350.0, 3.05, PERSON_B, -1, t, talk=0.8 if ph < -0.2 else 0.0, blink_ph=1.1)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    rrect(ctx, 150, 1050, 820, 380, 24)
    _stroke(ctx, 3.5, INK, 0.75 * q)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    fo = 1 - ease((t - T_Q) / 0.35)
    if fo > 0:
        ctx.push_group()
        draw_hist(ctx, t)
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

def pop(freq=520.0, dur=0.12):
    t = np.arange(int(core.SR * dur)) / core.SR
    return np.sin(2 * np.pi * (freq + 260 * np.exp(-t * 40)) * t) * np.exp(-t * 28) * 0.7


def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 174.6, 220.0, 293.7)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(3):                                      # 冒頭: ぽこ・ぽこ
        mx.add(0.1 + 0.45 * i, pop(480 + 80 * i), 0.3)
    mx.add(T_BUB_A, pop(700, 0.14), 0.35)                   # 吹き出し
    mx.add(T_BUB_B, pop(840, 0.14), 0.35)
    mx.add(T_MAP - 0.5, riser(0.8), 0.35)
    mx.add(T_RUN0 + 0.1, bell(988.0, 0.9), 0.4)             # 最初の1人
    beat(mx, T_RUN0 + T_RUN_HOLD, T_RUN1, bpm=132, vol=0.45, accel=True)
    mx.add(T_RUN1, thump(), 0.45)
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # 1万回の山
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
    for i in range(3):
        mx.add(T_TS1 + 0.1 * i, bell([784.0, 880.0, 988.0][i], 0.8), 0.35)
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


def run_checks():
    r = results()
    m_, main = r["m"], r["main"]
    y = solve_unheard()
    checks = []
    # (1) 条件・理論
    checks.append(("理論の見込み: 聞かないまま y の式 2(1−y) = −ln y の解 ≒ 0.2032", y, 0.2032, 0.0001))
    checks.append(("聞いた人の割合の中央値 m = 1 − y（町が大きいときの理論）", m_, 1 - y, 0.003))
    checks.append(("聞いた人の割合の平均も 1 − y（有限の町の ずれは小さい）", float(r["f"].mean()), 1 - y, 0.003))
    checks.append(("回の数 = 1万", float(len(main["heard"])), float(N_RUN), 0.0))
    checks.append(("町は 1万人（家 125×80 = 1万軒）", float(COLS * ROWS), float(N_TOWN), 0.0))
    checks.append(("聞いた人は 1人以上 町の人数以下", float(main["heard"].min() >= 1 and main["heard"].max() <= N_TOWN), 1.0, 0.0))
    for c in (2, 10):
        checks.append((f"1日に{c}人でも 聞かなかった人の割合の中央値は 理論 y（ひねりの文）", 1 - unheard_stats(r["by_c"][c])["med"], y, 0.003))
    ratio = unheard_stats(r["by_c"][2])["half_days"] / unheard_stats(r["by_c"][10])["half_days"]
    checks.append(("半分に届く日数の比（2人÷10人）≒ 5（人数に反比例）", ratio, 5.0, 0.3))
    hd = [unheard_stats(r["by_c"][c])["half_days"] for c in C_SHOW]
    checks.append(("人数が多いほど 半分に届くのが早い（ひねりの文）", float(hd[0] > hd[1] > hd[2]), 1.0, 0.0))
    # (2) 別の書き方との照合
    h_ag = run_agents(11, 3000, 300)
    h_ct = run_many(12, 3000, 1, 300)["heard"]
    checks.append(("小さい町(300人): 人を1人ずつ持つ書き方と 状態の数だけの書き方で 聞いた人の平均が同じ", float(h_ag.mean() / 300), float(h_ct.mean() / 300), 0.004))
    by20 = final_dist_exact(20, 20)
    exact_mean = sum(j * p for j, p in by20.items())
    sim20 = run_many(13, 40000, 1, 20)["heard"].mean()
    checks.append(("小さい町(20人): 式で出した 聞いた人数の平均 と 計算が同じ", float(sim20), float(exact_mean), 0.08))
    checks.append(("式の確率の合計 = 1（20人の町）", float(sum(by20.values())), 1.0, 1e-9))
    # (3) 同じ回を1つだけ回し直しても同じ（見本の照合の道具）
    ok = True
    for h in (0, 1, 2, 777, 9999):
        s_ = run_single(SEED_MAIN, h)
        ok = ok and s_["heard"] == main["heard"][h] and s_["steps"] == main["steps"][h] and s_["peak"] == main["peak"][h] \
            and abs(s_["t_half"] - main["t_half"][h]) < 1e-9 and abs(s_["t_end"] - main["t_end"][h]) < 1e-9
    checks.append(("回 0・1・2・777・9999 を1つだけ回し直しても 1万回の記録と同じ（聞いた人・歩数・最大・時刻）", float(ok), 1.0, 0.0))
    ks = run_keys(SEED_MAIN, np.arange(200000))
    u0, u1 = uni(ks, 3, 0), uni(ks, 3, 1)
    checks.append(("乱数: 0〜1の平均が 0.5", float(u0.mean()), 0.5, 0.003))
    checks.append(("乱数: 用途ちがいの相関が 0 に近い", float(np.corrcoef(u0, u1)[0, 1]), 0.0, 0.01))
    checks.append(("乱数: 回ちがいの相関が 0 に近い", float(np.corrcoef(u0[:-1], u0[1:])[0, 1]), 0.0, 0.01))
    # (4) 数字（画面に出る数）
    st = unheard_stats(main)
    checks.append(("全員（99%以上）に届いた回 = 回ごとの割合から数え直した数", float(st["full"]), float((main["heard"] >= FULL_F * N_TOWN).sum()), 0.0))
    checks.append(("最初の数人で止まった回 = 聞いた人が100人未満の回の数", float(st["early"]), float((main["heard"] < EARLY_N).sum()), 0.0))
    p_ex, _by = early_stop_exact()
    checks.append(("止まる確率（式）× 1万回 < 0.01（画面の「0回」と食い違わない）", float(p_ex * N_RUN < 0.01), 1.0, 0.0))
    checks.append(("止まる確率（式）の 言い方「約1億回に1回」", float(oku_text(p_ex) == "約1億回に1回"), 1.0, 0.0))
    h = main["heard"]
    checks.append(("いちばん届いた回/届かなかった回が 山の横軸（77〜82%）に収まる", float(h.min() / N_TOWN > H_LO and h.max() / N_TOWN < H_LO + H_NB * H_BIN), 1.0, 0.0))
    # (5) 答え
    key = answer_by_rule(m_)
    checks.append(("規則の答え = eight（約8割）", float(key == "eight"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が A（1番目）", float(INTRO.correct), 0.0, 0.0))
    checks.append(("記号の並び: 約8割・約9割・ほぼ全員 の順（数の3段階）", float(LABELS == ["約8割", "約9割", "ほぼ全員"]), 1.0, 0.0))
    for v_, k_ in ((0.80, "eight"), (0.85, "nine"), (0.90, "nine"), (0.95, "all"), (0.84999, "eight")):
        checks.append((f"規則の道具: m={v_:.5f} → {k_}", float(answer_by_rule(v_) == k_), 1.0, 0.0))
    # (6) 見本は1万回の中の1回そのもの
    S = samples()
    hh = S["h"]
    th, ts = S["th"], S["ts"]
    checks.append(("見本: 記録し直した聞いた人の数 = 1万回の記録", float(S["rec"]["heard"]), float(main["heard"][hh]), 0.0))
    checks.append(("見本: 記録し直した 半分に届いた時刻 = 1万回の記録", S["rec"]["t_half"], float(main["t_half"][hh]), 1e-9))
    checks.append(("見本: 人ごとの「聞いた時刻」の数 = 聞いた人の数", float(len(th)), float(main["heard"][hh]), 0.0))
    checks.append(("見本: 最後までに みんな話すのをやめた（やめた時刻がすべてある）", float(np.isfinite(ts).all()), 1.0, 0.0))
    checks.append(("見本: 聞いた時刻は 小さい順・やめた時刻は 聞いた時刻より あと", float(np.all(np.diff(th) >= 0) and np.all(ts >= th)), 1.0, 0.0))
    checks.append(("見本: 聞いた人の数が 1万回の中央値に ±5人以内", float(abs(main["heard"][hh] - S["med"]) <= 5), 1.0, 0.0))
    rs = run_state(T_RUN1)
    checks.append(("見本: 最後の画面の 知っている人 = 1万回の記録", float(rs["n"]), float(main["heard"][hh]), 0.0))
    checks.append(("見本: 最後の画面は 話している人 0人", float(rs["n_spread"]), 0.0, 0.0))
    checks.append(("見本: 最後の画面の灰色の家の数 = 町の人数 − 聞いた人", float((rs["cell"] == 0).sum()), float(N_TOWN - main["heard"][hh]), 0.0))
    mid = run_state(T_RUN0 + T_RUN_HOLD + 0.5 * (T_RUN1 - T_RUN0 - T_RUN_HOLD))
    checks.append(("見本: 途中の画面で 黄色 + 青 = 知っている人", float((mid["cell"] > 0).sum()), float(mid["n"]), 0.0))
    checks.append(("見本: 途中の画面で 黄色の数 = 話している人（聞いた − やめた）", float((mid["cell"] == 1).sum()), float(mid["n_spread"]), 0.0))
    r0 = run_state(T_RUN0)
    checks.append(("見本: はじめは 知っている人 1人・話している人 1人", float(r0["n"] + r0["n_spread"]), 2.0, 0.0))
    checks.append(("見本: 家の位置は 1軒に1人（重ならない）", float(len(set(S["pos"].tolist()))), float(N_TOWN), 0.0))
    # (7) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    s_top = min(56.0, 100.0 * 850.0 / wmax)
    checks.append(("上の問い2行: 文字は24px以上", float(s_top >= 24), 1.0, 0.0))
    # (8) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本の1回が止まったあと 次の場面まで 3秒以上", float(T_D0 - T_RUN1 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 山の数字（答えまで）3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: ひねりの棒の数字 3秒以上", float(T_Q - T_TS1 >= 3.0), 1.0, 0.0))
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
    rec = S["rec"]
    print(f"長さ {DURATION:.1f}秒  立ち話 {T_GO:.1f}-{T_MAP:.1f}  町の図 {T_MAP:.1f}  見本の進み {T_RUN0 + T_RUN_HOLD:.1f}〜{T_RUN1:.1f}  山 {T_D0:.1f}-{T_D1:.1f}  "
          f"数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: 回 #{S['h']}  聞いた {rec['heard']}人  聞かなかった {N_TOWN - rec['heard']}人（{pct((N_TOWN - rec['heard']) / N_TOWN)}%）  "
          f"半分に届く {rec['t_half']:.2f}日  止まるまで {rec['t_end']:.2f}日  出来事 {len(S['ev'])}回")
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
        tr = lambda u: T_RUN0 + T_RUN_HOLD + u * (T_RUN1 - T_RUN0 - T_RUN_HOLD)         # noqa: E731
        ts_ = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_GO + 1.0, T_MAP - 0.3, T_RUN0 + 0.5, T_RUN0 + T_RUN_HOLD + 0.1, tr(0.04), tr(0.12),
               tr(0.3), tr(0.6), T_RUN1 - 0.1, T_RUN1 + 1.5, T_D0 + 1.5, T_D1 - 0.2, T_DN + 1.2, T_DN2 + 1.2, T_REV + 0.9, T_ANS2 + 0.6,
               T_TW + 0.8, T_TW + 2.4, T_TS1 + 1.2, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts_, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
