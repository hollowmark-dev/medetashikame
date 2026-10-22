"""3階まで、階段とエレベーター、どっちが早い？ 1階から同時にスタートして1万回。— 2026-10-17 作成（公開予定 10/22）

モデル（ふつうのビル。5〜8階建て・エレベーター1台。1回ごとに建物・人・エレベーターをでたらめに変える）
  建物     : 階数 5〜8（等確率）。1階ぶんの高さ 3.0〜4.0m（一様）。
  階段     : 高さ方向の速さ（踊り場の折り返しも込みの、高さ ÷ かかった時間）。
             対数正規で 真ん中 0.24 m/秒・ばらつき（対数の標準偏差）0.20、0.14〜0.40 で切る（25〜75% は おおよそ 0.21〜0.28）。
             ・Ronchi ほか 2015（Lund 大学の報告書。自分のペースで上る実験、高さ方向の速さ＝踊り場込み）: 真ん中 0.24 m/秒、
               25% 約0.19〜0.20・75% 約0.26〜0.30（Kista の建物）。もう1つの建物（Ideon）は 0.28〜0.35。
             ・同報告書の表: 駅の短い階段で通勤客の高さ方向 0.27〜0.32 m/秒（Yeo & He 2009）。
             ・このチャンネルのエスカレーターのロング（10/21）は 階段を高さ方向 0.2 / 0.25 m/秒 で比べた。この回の真ん中 0.24 はその間に入る。
             下り（ひねり）: 上りの速さ × 1.20〜1.45（一様）。階避難安全検証法の告示（平成12年建設省告示第1441号）の歩行速度は
             階段で 上り27・下り36 m/分（劇場・共同住宅など）、上り35・下り47 m/分（事務所など）で、どちらも 下り÷上り ≒ 1.33。
  エレベーター:
             定格速度 45〜90 m/分（一様。一般に 45〜105 m/分）。加速度 0.6〜1.0 m/秒²（Powell 2008 の例は 3 ft/秒² ≒ 0.91）。
             動き出しの遅れ（ブレーキが外れて動き出すまで・着床の合わせ）0.5〜1.0 秒。移動は 加速→一定→減速（台形）。
             ドア: 開く 1.5〜3.0 秒、閉まる 2.0〜3.5 秒（Powell 2008 の例は 開 2.0・閉 3.0。幅800mmの速い戸で 開1.5・閉2.0）。
             乗る 1.2 秒/人・降りる 1.0 秒/人（Powell 2008）。最後の人が通ってから閉まり始めるまで 1.0〜2.5 秒。
             3階で「着いた」＝ ドアが開ききってから 1.0 秒で降りた時点。階段は 3階の床に着いた時点。
  ボタンを押したときのかご（1回ごとに1つ。重みは仮定）:
             S1 30%: 1階で止まっている（ドアは閉まっている）→ すぐ開く
             S2 30%: ほかの階（2階〜最上階から等確率）で止まっている → 1階へ来る
             S3 40%: ほかの人を運んでいる。いまの階（1〜最上階）・向きはでたらめ。今の作業の残り 0〜4 秒。
                 上り中: 上の階 1〜2 か所で人を降ろしてから、1階へ下りてくる
                 下り中: 1階まで行く（途中の階で 30% の確率でもう1回止まる）。1階で 1〜3人 が降りてから乗る
                 下りてくる途中の各階で 10% の確率で ほかの人に呼ばれて止まる（1人乗る）
             乗ったあと: 10% で 2階にも止まる（いっしょに乗った人・2階で呼んだ人）。
             → 待ち時間（ボタンから 1階のドアが開き始めるまで）の平均は 16.9秒・真ん中 11.8秒（--model で出す）。
               事務所の設計目標の平均待ち 約20秒（業界の目安）より少し短い（エレベーターに少し甘い）。共同住宅の混む時間の目安は 運転間隔 40〜80秒（Powell 2008）。
  下り（ひねり）: 3階 → 1階。同じ建物・同じ人・同じかごの状態で、3階で下りのボタンを押す。
             上り中のかごは上の用事をすませてから3階へ、下り中のかごは 3階より上にいれば途中で拾い、下にいれば1階まで行ってから上がってくる。

問い: 「階段とエレベーター、/ 3階まで、どっちが早い？」 A 階段 ／ B ほぼ同じ ／ C エレベーター
      （2026-10-17 計算のあと、正解の記号が前日 10/21 の A と続かないよう選択肢の並びだけ入れ替えた。規則と計算は変えていない）
答えの決め方（計算の前に決めた規則。answer_by_rule）:
      1万回のうち「階段の人が先に3階に着いた回」の割合 p と、着いた時刻の差（エレベーター − 階段）の真ん中の値 g で、
      p ≥ 60% かつ g ≥ 5秒 なら A、p ≤ 40% かつ g ≤ −5秒 なら B、それ以外は C。
ひねり: 「では、下りなら？」 3階 → 1階 を 同じ1万回で。
締め: 「あなたは、何階からエレベーター？」（答えは出さない。分かれ目の階は画面にも概要欄にも出さない）

結果（SEED_MAIN）: 階段が先 59.7%（5,969回）、差の真ん中 +4.2秒 → C（ほぼ同じ）。種を変えても 58.9〜59.6%・+3.8〜+4.2秒で C。
      かごの状態で分かれる: 1階で止まっていた回は 階段が先 9%、ほかの階で止まっていた回 67%、運転中 93%。
      下り: 階段が先 88.8%、差の真ん中 +10.4秒。

乱数の種は見本（並んで上る2人）の見栄えのために選んでよい。答えの統計は1万回すべてから正直に出す。
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "kaidan-elevator"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- モデルの値 ----------
N_TRIAL = 10000
FLOORS = (5, 8)                                   # 階数（両端を含む）
FLOOR_H = (3.0, 4.0)                              # 1階ぶんの高さ（m）
STAIR_MED, STAIR_SIG, STAIR_CLIP = 0.24, 0.20, (0.14, 0.40)   # 階段（上り・高さ方向 m/秒）
DOWN_RATIO = (1.20, 1.45)                         # 下りの速さ ÷ 上りの速さ
SPEED = (45.0, 90.0)                              # 定格速度（m/分）
ACC = (0.6, 1.0)                                  # 加速度（m/秒²）
START = (0.5, 1.0)                                # 動き出しの遅れ（秒）
T_OPEN = (1.5, 3.0)                               # ドアが開く（秒）
T_CLOSE = (2.0, 3.5)                              # ドアが閉まる（秒）
T_IN, T_OUT = 1.2, 1.0                            # 乗る・降りる（秒/人）
DWELL = (1.0, 2.5)                                # 最後の人が通ってから閉まり始めるまで（秒）
P_SCEN = (0.30, 0.30, 0.40)                       # S1 1階で停止 / S2 ほかの階で停止 / S3 運転中
RESID = (0.0, 4.0)                                # S3 の今の作業の残り（秒）
P_HALL = 0.10                                     # 下りてくる途中の各階で呼ばれる確率
P_MID_DOWN = 0.30                                 # 下り中のかごが途中でもう1回止まる確率
P_RIDE2 = 0.10                                    # 乗ったあと 2階にも止まる確率
ORIGIN, DEST = 1, 3

# ---------- 答えの規則（計算の前に決めた） ----------
RULE_HI, RULE_LO, RULE_GAP = 0.60, 0.40, 5.0


def answer_by_rule(p_stairs, gap_med):
    """p_stairs = 階段の人が先に着いた回の割合、gap_med = (エレベーター − 階段) の着いた時刻の差の真ん中の値（秒）"""
    if p_stairs >= RULE_HI and gap_med >= RULE_GAP:
        return 0                                  # A 階段
    if p_stairs <= RULE_LO and gap_med <= -RULE_GAP:
        return 2                                  # C エレベーター
    return 1                                      # B ほぼ同じ


# ---------- 1回ぶんの値 ----------

def draw_trial(rng):
    u = lambda lo_hi: float(rng.uniform(lo_hi[0], lo_hi[1]))   # noqa: E731
    n = int(rng.integers(FLOORS[0], FLOORS[1] + 1))
    v_up = float(np.clip(STAIR_MED * math.exp(rng.normal(0, STAIR_SIG)), *STAIR_CLIP))
    p = dict(n=n, hf=u(FLOOR_H), v_up=v_up, v_down=v_up * u(DOWN_RATIO),
             v=u(SPEED) / 60.0, acc=u(ACC), start=u(START), t_open=u(T_OPEN), t_close=u(T_CLOSE), dwell=u(DWELL))
    s = int(rng.choice(3, p=P_SCEN))
    p["scen"] = s
    p["resid"] = u(RESID)
    p["hall"] = rng.uniform(0, 1, 10) < P_HALL      # 各階（添字＝階）で ほかの人に呼ばれるか
    p["ride2"] = bool(rng.uniform() < P_RIDE2)
    p["n_exit"] = int(rng.integers(1, 4))
    if s == 0:
        p["f0"], p["dir"] = 1, 0
    elif s == 1:
        p["f0"], p["dir"] = int(rng.integers(2, n + 1)), 0
    else:
        f0 = int(rng.integers(1, n + 1))
        d = 1 if rng.uniform() < 0.5 else -1
        if f0 == n:
            d = -1
        if f0 == 1:
            d = 1
        p["f0"], p["dir"] = f0, d
        if d == 1:
            k = min(int(rng.integers(1, 3)), n - f0)
            p["stops"] = sorted(int(x) for x in rng.choice(np.arange(f0 + 1, n + 1), k, replace=False))
        else:
            mid = [int(rng.integers(2, f0))] if (f0 > 2 and rng.uniform() < P_MID_DOWN) else []
            p["stops"] = mid + [1]
    return p


def flight(d, v, a):
    """距離 d（m）を 加速→一定→減速 で動く時間（動き出しの遅れは含まない）"""
    if d <= 0:
        return 0.0
    if d >= v * v / a:
        return d / v + v / a
    return 2 * math.sqrt(d / a)


def flight_pos(t, d, v, a):
    """動き出してから t 秒の位置（0〜d）"""
    T = flight(d, v, a)
    t = max(0.0, min(t, T))
    if d >= v * v / a:
        ta = v / a
        if t < ta:
            return 0.5 * a * t * t
        if t < T - ta:
            return 0.5 * a * ta * ta + v * (t - ta)
        r = T - t
        return d - 0.5 * a * r * r
    th = T / 2
    if t < th:
        return 0.5 * a * t * t
    r = T - t
    return d - 0.5 * a * r * r


class Car:
    """かごの動きを順に記録する。log は ('wait', t0, t1, 階) / ('move', t0, t1, 階から, 階へ) / ('stop', t0, t1, 階, 開き終わり, 閉まり始め)"""

    def __init__(self, p, f, t=0.0):
        self.p, self.f, self.t = p, f, t
        self.log = []

    def wait(self, dt):
        if dt > 0:
            self.log.append(("wait", self.t, self.t + dt, self.f))
            self.t += dt

    def move(self, to):
        if to == self.f:
            return
        p = self.p
        dt = p["start"] + flight(abs(to - self.f) * p["hf"], p["v"], p["acc"])
        self.log.append(("move", self.t, self.t + dt, self.f, to))
        self.t += dt
        self.f = to

    def stop(self, n_out, n_in, mine=False):
        """ドアを開けて n_out 人降り、n_in 人乗り、閉める。mine=True なら（自分が降りる）開いて降りたところで返す"""
        p = self.p
        t0 = self.t
        t_open_end = t0 + p["t_open"]
        if mine:
            t_close0 = t_open_end + n_out * T_OUT + p["dwell"]
            self.log.append(("stop", t0, t_close0 + p["t_close"], self.f, t_open_end, t_close0))
            self.t = t_close0 + p["t_close"]
            return dict(open0=t0, open1=t_open_end, out=t_open_end + T_OUT)
        t_close0 = t_open_end + n_out * T_OUT + n_in * T_IN + p["dwell"]
        self.log.append(("stop", t0, t_close0 + p["t_close"], self.f, t_open_end, t_close0))
        self.t = t_close0 + p["t_close"]
        return dict(open0=t0, open1=t_open_end, close0=t_close0, close1=self.t)


def elevator(p, origin, dest):
    """origin で呼んで dest で降りるまで。返り値: 着いた時刻・内わけ・かごの記録・人の出来事"""
    s, f0, d = p["scen"], p["f0"], p["dir"]
    car = Car(p, f0)
    carried = []                                   # 自分が乗ったあとも残るほかの人の行き先（下りのとき）
    n_exit = 0
    going_down = dest < origin
    if s == 2:
        car.wait(p["resid"])
        if d == 1:                                 # 上り中: 上の用事 → 呼ばれた階へ
            stops = p["stops"]
            for k, fl in enumerate(stops):
                car.move(fl)
                if fl == origin and k == len(stops) - 1 and going_down:
                    n_exit = 1                     # いちばん上の用事が自分の階: そこで1人降ろし、向きを変えて拾う
                    break
                car.stop(1, 0)
            if car.f != origin:
                top = car.f
                lo, hi = (origin + 1, top - 1) if top > origin else (top + 1, origin - 1)
                for fl in (range(hi, lo - 1, -1) if top > origin else range(lo, hi + 1)):
                    if p["hall"][fl] and top > origin:
                        car.move(fl)
                        car.stop(0, 1)
                        if origin == 1:
                            n_exit += 1            # 1階で降りる人（下りなら自分といっしょに1階まで乗っていく）
                car.move(origin)
        else:                                      # 下り中
            stops = p["stops"]
            if going_down and f0 > origin:         # 自分の階より上: 途中で拾う
                for fl in range(f0 - 1, origin, -1):
                    if fl in stops or p["hall"][fl]:
                        car.move(fl)
                        car.stop(1 if fl in stops else 0, 0 if fl in stops else 1)
                car.move(origin)
                carried = [fl for fl in stops if fl < origin] + [fl for fl in range(origin - 1, 1, -1) if p["hall"][fl]]
                n_exit = 1 if origin in stops else 0
            else:                                  # 1階まで行ってから
                for fl in range(f0 - 1, 1, -1):
                    if fl in stops or p["hall"][fl]:
                        car.move(fl)
                        car.stop(1 if fl in stops else 0, 0 if fl in stops else 1)
                        if not (fl in stops):
                            n_exit += 1
                car.move(1)
                if origin == 1:
                    n_exit += p["n_exit"]
                else:
                    car.stop(p["n_exit"] + n_exit, 0)
                    n_exit = 0
                    car.move(origin)
    else:
        car.move(origin)                           # S1 はすでに origin にいる（上り）。下りなら 1階から上がってくる
    # 自分が乗る
    t_called_open = car.t                          # ここで origin のドアが開き始める
    board = car.stop(n_exit, 1)
    t_wait = board["open0"]
    # 乗っている間
    ride_stops = set()
    if p["ride2"]:
        ride_stops.add(2)
    if going_down:
        ride_stops |= {fl for fl in carried if fl not in (origin, dest)}
    rng_dir = range(origin + 1, dest) if dest > origin else range(origin - 1, dest, -1)
    n_mid = 0
    for fl in rng_dir:
        if fl in ride_stops:
            car.move(fl)
            car.stop(1, 0)
            n_mid += 1
    car.move(dest)
    out = car.stop(1, 0, mine=True)
    t_arr = out["out"]
    door = (board["close1"] - board["open0"]) + n_mid * 0 + (out["out"] - out["open0"])
    mid_stop_time = sum(e[2] - e[1] for e in car.log if e[0] == "stop" and board["close1"] <= e[1] < out["open0"])
    door += mid_stop_time
    moving = t_arr - t_wait - door
    return dict(t=t_arr, wait=t_wait, door=door, move=moving, log=car.log, board=board, out=out,
                t_called_open=t_called_open, n_exit=n_exit, n_mid=n_mid)


def stairs(p, origin, dest):
    h = abs(dest - origin) * p["hf"]
    v = p["v_up"] if dest > origin else p["v_down"]
    return h / v


def run(seed, n=N_TRIAL):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        p = draw_trial(rng)
        eu = elevator(p, ORIGIN, DEST)
        ed = elevator(p, DEST, ORIGIN)
        rows.append((p["n"], p["hf"], p["v_up"], p["v_down"], p["v"], p["scen"], p["f0"], p["dir"],
                     stairs(p, ORIGIN, DEST), eu["t"], eu["wait"], eu["door"], eu["move"],
                     stairs(p, DEST, ORIGIN), ed["t"], ed["wait"]))
    a = np.array(rows, float)
    keys = ["n", "hf", "v_up", "v_down", "v", "scen", "f0", "dir", "st_u", "el_u", "wait_u", "door_u", "move_u",
            "st_d", "el_d", "wait_d"]
    return {k: a[:, i] for i, k in enumerate(keys)}


def trial_params(seed, i):
    """1万回のうち i 回目の値（run と同じ順に乱数を引き直す）"""
    rng = np.random.default_rng(seed)
    for _ in range(i):
        draw_trial(rng)
    return draw_trial(rng)


SEED_MAIN = 20261022
_RES = {}


def results():
    if not _RES:
        cache = OUT / "cache" / f"model_{SEED_MAIN}.npz"
        if cache.exists():
            _RES["m"] = dict(np.load(cache))
        else:
            r = run(SEED_MAIN)
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez(cache, **r)
            _RES["m"] = r
    return _RES["m"]


def shown():
    r = results()
    gu = r["el_u"] - r["st_u"]
    gd = r["el_d"] - r["st_d"]
    win_u = r["st_u"] < r["el_u"]
    win_d = r["st_d"] < r["el_d"]
    sc = r["scen"]
    return dict(p_up=float(np.mean(win_u)), n_st=int(win_u.sum()), n_el=int((r["el_u"] < r["st_u"]).sum()),
                gap_med=float(np.median(gu)), gap_mean=float(gu.mean()), gap_q=np.percentile(gu, [10, 25, 75, 90]),
                med_st=float(np.median(r["st_u"])), med_el=float(np.median(r["el_u"])),
                mean_st=float(r["st_u"].mean()), mean_el=float(r["el_u"].mean()),
                mean_wait=float(r["wait_u"].mean()), med_wait=float(np.median(r["wait_u"])),
                mean_door=float(r["door_u"].mean()), mean_move=float(r["move_u"].mean()),
                p_down=float(np.mean(win_d)), gap_d_med=float(np.median(gd)), med_st_d=float(np.median(r["st_d"])),
                med_el_d=float(np.median(r["el_d"])), mean_wait_d=float(r["wait_d"].mean()),
                by_scen=[(float(np.mean(win_u[sc == k])), float(np.median(gu[sc == k])), int((sc == k).sum()))
                         for k in range(3)],
                by_scen_d=[(float(np.mean(win_d[sc == k])), float(np.median(gd[sc == k]))) for k in range(3)],
                v_q=np.percentile(r["v_up"], [25, 50, 75]))


def report():
    sh = shown()
    print(f"上り: 階段が先 {sh['p_up']:.4f}（{sh['n_st']}回 / エレベーターが先 {sh['n_el']}回）  差の中央値 {sh['gap_med']:+.2f}秒  "
          f"平均 {sh['gap_mean']:+.2f}  10/25/75/90% {np.round(sh['gap_q'], 1)}")
    print(f"  答え {'ABC'[answer_by_rule(sh['p_up'], sh['gap_med'])]}")
    print(f"  中央値 階段 {sh['med_st']:.1f}秒 / エレベーター {sh['med_el']:.1f}秒   平均 {sh['mean_st']:.1f} / {sh['mean_el']:.1f}")
    print(f"  エレベーターの内わけ（平均）待つ {sh['mean_wait']:.1f}（中央値 {sh['med_wait']:.1f}）・ドアと乗り降り {sh['mean_door']:.1f}"
          f"・動く {sh['mean_move']:.1f}")
    for k, (pp, gg, nn) in enumerate(sh["by_scen"]):
        print(f"  S{k + 1}（{nn}回）: 階段が先 {pp:.3f}  差の中央値 {gg:+.1f}")
    print(f"下り: 階段が先 {sh['p_down']:.4f}  差の中央値 {sh['gap_d_med']:+.2f}秒  中央値 階段 {sh['med_st_d']:.1f} / "
          f"エレベーター {sh['med_el_d']:.1f}  待ち平均 {sh['mean_wait_d']:.1f}")
    for k, (pp, gg) in enumerate(sh["by_scen_d"]):
        print(f"  S{k + 1}: 階段が先 {pp:.3f}  差の中央値 {gg:+.1f}")
    print(f"階段の速さ 25/50/75% {np.round(sh['v_q'], 3)}")


if __name__ == "__main__" and "--model" in sys.argv:
    report()
    sys.exit(0)


# =====================================================================
# 見本（並んで上る2人）を選ぶ
# =====================================================================
_SAMPLE = None


def all_params(seed, n):
    rng = np.random.default_rng(seed)
    return [draw_trial(rng) for _ in range(n)]


def sample():
    """見本: 1万回の中から選ぶ（その回の値そのもの）。
    条件: 結果が多数派と同じ向き（階段が先）で、差が真ん中の値の近く（±1秒）。5階建て・かごは4〜5階で止まっていた（S2）。
    乗ったあと2階に止まらない。その中で、高さと階段の速さが真ん中に近い回"""
    global _SAMPLE
    if _SAMPLE is not None:
        return _SAMPLE
    r = results()
    sh = shown()
    gap = r["el_u"] - r["st_u"]
    cand = np.nonzero((gap > 0) & (np.abs(gap - sh["gap_med"]) < 1.0) & (r["scen"] == 1) & (r["n"] == 5)
                      & (r["f0"] >= 4))[0]
    if len(cand) == 0:
        raise SystemExit("見本の候補がない")
    params = all_params(SEED_MAIN, int(cand.max()) + 1)
    best, score = None, 1e9
    for i in cand:
        p = params[i]
        if p["ride2"]:
            continue
        sc = abs(p["hf"] - 3.5) / 0.5 + abs(p["v_up"] - STAIR_MED) / 0.04 + abs(gap[i] - sh["gap_med"])
        if sc < score:
            best, score = int(i), sc
    if best is None:
        raise SystemExit("見本の候補がない")
    p = params[best]
    e = elevator(p, ORIGIN, DEST)
    assert abs(e["t"] - r["el_u"][best]) < 1e-6 and abs(stairs(p, ORIGIN, DEST) - r["st_u"][best]) < 1e-6
    _SAMPLE = dict(i=best, p=p, e=e, t_st=stairs(p, ORIGIN, DEST), t_el=e["t"], gap=float(gap[best]))
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    s = sample()
    p = s["p"]
    print("見本", s["i"], "階", p["n"], "高さ", round(p["hf"], 2), "階段", round(p["v_up"], 3), "かご", p["f0"], "速さ",
          round(p["v"] * 60), "m/分  階段", round(s["t_st"], 1), "エレベーター", round(s["t_el"], 1), "待つ", round(s["e"]["wait"], 1))
    for ev in s["e"]["log"]:
        print("   ", ev[0], [round(x, 2) if isinstance(x, float) else x for x in ev[1:]])
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
note.DATE = "10.22"                               # 日付欄（公開予定日）

COL_A, INK_A = "#f4ad6a", "#b8601a"               # A 階段（橙）
COL_B, INK_B = "#8fbbe8", "#2f63a8"               # B エレベーター（青）
COL_D = "#e0874a"                                 # 下り（ひねり）の棒
WALL = "#d9d2c2"
SLAB = "#c9bfa9"
CAR = "#fff6d8"
SHAFT = "#e6e1d5"

# ---------- 時間割（動画の秒） ----------
T_CD = (2.75, 3.75, 4.75, 5.75, 6.75, 7.75)       # 5・4・3・2・1・0（0で止める）
T_GO = T_CD[-1] + 0.6
T_MOVE = T_GO - 0.4
INTRO_X = 1.0                                     # 冒頭は実際の速さ
SLOW_X = 1.4                                      # 着く前はゆっくり
SLOW_SPAN = 4.5                                   # 先に着く人の何秒前（実際の秒）からゆっくりにするか
RACE_LEN = 11.5                                   # T_GO から2人とも着くまで（動画の秒）
BIG_Q = ["階段とエレベーター、", "3階まで どっちが早い？"]
DETAIL = "1階から同時にスタート。エレベーターは1台"
LABELS = ["階段", "ほぼ同じ", "エレベーター"]
CORRECT = 1                                       # answer_by_rule で計算結果から決めた答え。ずれたら run_checks が止める
NAME = {"a": "階段", "b": "エレベーター"}
TAG = {"a": "A", "b": "C"}
COL = {"a": COL_A, "b": COL_B}
INKC = {"a": INK_A, "b": INK_B}

# 場面（場面の座標: 幅1080・高さ SCENE_H。画面へは layout で縮めて置く）
SCENE_H = 760.0
CX = 580.0
GROUND = 735.0                                    # 1階の床
FH = 135.0                                        # 1階ぶん（場面の px）
BX0, BX1 = 150.0, 975.0                           # 建物の左右の壁
ST_X1 = 470.0                                     # 階段室の右の壁
FL_A, FL_B, LAND_R = 215.0, 395.0, 455.0          # 階段の下端・上端・中の踊り場の右端
SH_X0, SH_X1 = 770.0, 975.0                       # 昇降路
CAR_X0, CAR_X1 = 784.0, 926.0                     # かご
CAR_H = 112.0
DOOR_H = 104.0
P_H = 100.0                                       # 人の高さ
B_WAIT_X = 690.0                                  # エレベーターを待つ位置
B_RIDE_X = 860.0                                  # かごの中の位置
BTN_X = 742.0
LAY_INTRO = (1.0, 690.0)                          # (縮める倍率, 場面の上端の y)
LAY_RACE = (0.75, 572.0)
ZOOM0, ZOOM_T = 1.38, 1.5                         # 0秒目は1階に寄っていて、1.5秒で引く
ZOOM_F = (560.0, GROUND)


def floor_y(k):
    """k 階の床の y（場面）"""
    return GROUND - (k - 1) * FH


def setup():
    global TL, RACE_X, T_FIN1, T_FIN2, T_RACE_END, T_G0, T_G1, T_REV, T_WHY, T_TW, T_TW_RUN, T_Q, DURATION
    s = sample()
    f1, f2 = sorted((s["t_st"], s["t_el"]))

    def build(rx):
        ts = np.arange(0, 80, 1 / 300)
        tau = np.zeros_like(ts)
        v = 0.0
        for k in range(1, len(ts)):
            t = ts[k]
            if t < T_GO:
                sp = INTRO_X
            else:
                sp = INTRO_X + (rx - INTRO_X) * ease((t - T_GO) / 0.8)
                if v > f1 - SLOW_SPAN:
                    sp = min(sp, SLOW_X)
            v += sp / 300
            tau[k] = v
        return ts, tau

    lo, hi = 1.0, 30.0
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
    T_RACE_END = T_FIN2 + 2.2                     # 着いた付箋を読む時間
    T_G0 = T_RACE_END                             # 1万回のマス目
    T_G1 = T_G0 + 2.4
    T_REV = T_G1 + 0.8                            # 答え
    T_WHY = T_REV + 3.6                           # なぜ（かごがどこにいたか）
    T_TW = T_WHY + 4.6                            # ひねり
    T_TW_RUN = T_TW + 2.2
    T_Q = T_TW_RUN + 5.0                          # 締め
    DURATION = T_Q + 4.2


def tau_of(t):
    return float(np.interp(t, TL["t"], TL["tau"]))


def t_of(tau):
    """実際の秒 τ → 動画の秒"""
    return float(np.interp(tau, TL["tau"], TL["t"]))


def speed_now(t):
    return (tau_of(t + 0.02) - tau_of(t - 0.02)) / 0.04 if t > 0.03 else INTRO_X


# ---------- 2人とかごの状態（実際の秒 τ で） ----------

def car_state(tau):
    """かごの位置（階。小数）・動いている向き・各階のドアの開き具合 {階: 0〜1}"""
    s = sample()
    log, p = s["e"]["log"], s["p"]
    pos, mv, doors = float(p["f0"]), 0, {}
    for ev in log:
        kind, t0, t1 = ev[0], ev[1], ev[2]
        if tau < t0:
            break
        if kind == "wait":
            pos = float(ev[3])
        elif kind == "move":
            a, b = ev[3], ev[4]
            if tau >= t1:
                pos, mv = float(b), 0
                continue
            d = abs(b - a) * p["hf"]
            x = flight_pos(tau - t0 - p["start"], d, p["v"], p["acc"]) if tau - t0 > p["start"] else 0.0
            pos = a + (b - a) * x / d
            mv = 1 if b > a else -1
        elif kind == "stop":
            fl, o1, c0 = ev[3], ev[4], ev[5]
            pos, mv = float(fl), 0
            if tau < t1:
                if tau < o1:
                    o = (tau - t0) / (o1 - t0)
                elif tau < c0:
                    o = 1.0
                else:
                    o = 1 - (tau - c0) / (t1 - c0)
                doors[fl] = ease(clamp01(o))
    return pos, mv, doors


def stair_state(tau):
    """階段の人: 場面の足元 (x, y)・向き（1 右 / −1 左）・歩いているか・高さ（階ぶん。0〜2）"""
    T = sample()["t_st"]
    unit = T / 3.8                                # 階段4本（0.8ずつ）＋ 折り返し3回（0.2ずつ）
    half = FH / 2
    if tau >= T:
        dt = tau - T
        return dict(x=FL_A - 34 * clamp01(dt / 1.0), y=floor_y(3), face=-1, walk=dt < 1.0, h=2.0, done=True)
    u = tau / unit
    for j in range(4):
        y0 = GROUND - j * half
        right = j % 2 == 0
        if u < 0.8:
            k = u / 0.8
            x = FL_A + (FL_B - FL_A) * k if right else FL_B - (FL_B - FL_A) * k
            return dict(x=x, y=y0 - half * k, face=1 if right else -1, walk=True, h=(j + k) / 2, done=False)
        u -= 0.8
        if j < 3:
            if u < 0.2:
                k = u / 0.2
                x = FL_B + 30 * math.sin(math.pi * k) if right else FL_A - 30 * math.sin(math.pi * k)
                face = (1 if k < 0.5 else -1) if right else (-1 if k < 0.5 else 1)
                return dict(x=x, y=y0 - half, face=face, walk=True, h=(j + 1) / 2, done=False)
            u -= 0.2
    return dict(x=FL_A, y=floor_y(3), face=-1, walk=False, h=2.0, done=True)


def elev_state(tau):
    """エレベーターの人: 場面の足元 (x, y)・向き・歩いているか・手をのばすか・いる階・様子"""
    e = sample()["e"]
    pos, mv, doors = car_state(tau)
    b, o = e["board"], e["out"]
    cy = GROUND - (pos - 1) * FH
    if tau < 0.9:                                 # ボタンを押す
        return dict(x=B_WAIT_X, y=GROUND, face=1, walk=False, reach=math.sin(math.pi * clamp01(tau / 0.9)), fl=1,
                    status="wait", done=False)
    if tau < b["open1"]:
        return dict(x=B_WAIT_X, y=GROUND, face=1, walk=False, reach=0.0, fl=1, status="wait", done=False)
    if tau < b["open1"] + T_IN:                   # 乗りこむ
        k = (tau - b["open1"]) / T_IN
        return dict(x=B_WAIT_X + (B_RIDE_X - B_WAIT_X) * ease(k), y=GROUND, face=1, walk=True, reach=0.0, fl=1,
                    status="board", done=False)
    if tau < o["open1"]:
        st = "ride" if mv != 0 else "door"
        return dict(x=B_RIDE_X, y=cy, face=-1, walk=False, reach=0.0, fl=int(math.floor(pos + 1e-6)), status=st,
                    done=False)
    if tau < o["out"]:                            # 降りる
        k = (tau - o["open1"]) / T_OUT
        return dict(x=B_RIDE_X + (740 - B_RIDE_X) * k, y=floor_y(3), face=-1, walk=True, reach=0.0, fl=3,
                    status="out", done=False)
    dt = tau - o["out"]
    return dict(x=740 - 50 * clamp01(dt / 0.8), y=floor_y(3), face=-1, walk=dt < 0.8, reach=0.0, fl=3,
                status="done", done=True)


# ---------- 場面の置き場所 ----------

def layout(t):
    m = ease(clamp01((t - T_MOVE) / (T_GO - T_MOVE)))
    return (LAY_INTRO[0] + (LAY_RACE[0] - LAY_INTRO[0]) * m, LAY_INTRO[1] + (LAY_RACE[1] - LAY_INTRO[1]) * m)


def zoom(t):
    return 1 + (ZOOM0 - 1) * (1 - ease(t / ZOOM_T))


def to_dev(t, x, y):
    sc, y0 = layout(t)
    z = zoom(t)
    fx, fy = ZOOM_F
    x2, y2 = fx + (x - fx) * z, fy + (y - fy) * z
    return CX + (x2 - CX) * sc, y0 + y2 * sc


def scene_scale(t):
    return layout(t)[0] * zoom(t)


def apply_scene(ctx, t):
    sc, y0 = layout(t)
    z = zoom(t)
    fx, fy = ZOOM_F
    ctx.translate(CX * (1 - sc), y0)
    ctx.scale(sc, sc)
    ctx.translate(fx * (1 - z), fy * (1 - z))
    ctx.scale(z, z)


def scene_box(t):
    sc, y0 = layout(t)
    return CX * (1 - sc), y0, W * sc, SCENE_H * sc


def stext(ctx, t, s, x, y, size, color=INK, align="center", alpha=1.0, bold=True):
    """場面の中の字（画面の座標に直して描く。iPhone で切れる所・場面の外では出さない）"""
    xd, yd = to_dev(t, x, y)
    sz = max(24.0, size * scene_scale(t))
    w = core.text_width(s, sz)
    x0 = xd - w / 2 if align == "center" else (xd if align == "left" else xd - w)
    bx, by, bw, bh = scene_box(t)
    if x0 < 76 or x0 + w > 1004 or yd - sz / 2 < max(by, 372) or yd + sz / 2 > min(by + bh, 1448):
        return
    if yd + sz / 2 > 1000 and x0 + w > 928:
        return
    text(ctx, s, xd, yd, sz, color, align=align, alpha=alpha, bold=bold)


# ---------- 絵: 人（ペン描きの線） ----------

def _limb(ctx, pts, w, col, ink=INK, a=1.0):
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(ink, a))
    for dx, dy in ((0.7, -0.5), (-0.6, 0.8)):
        ctx.set_line_width(w + 4.0)
        ctx.move_to(pts[0][0] + dx, pts[0][1] + dy)
        for q in pts[1:]:
            ctx.line_to(q[0] + dx, q[1] + dy)
        ctx.stroke()
    c = hexrgb(col, a) if isinstance(col, str) else (col[0], col[1], col[2], a)
    ctx.set_source_rgba(*c)
    ctx.set_line_width(w)
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.stroke()


def _dark(col, k=0.82):
    c = hexrgb(col)
    return (c[0] * k, c[1] * k, c[2] * k, 1.0)


def draw_person(ctx, x, gy, h, col, phase, amp=1.0, face=1, reach=0.0, climb=0.0):
    """横から見た歩く人。足元が (x, gy)。face=1 で右向き。reach で前の手を上げる（ボタン）。climb で膝を高く上げる（階段）"""
    s = h / 150.0
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(s * face, s)
    lean = 0.05 + 0.07 * climb
    A_leg = 0.42 * amp
    A_arm = 0.45 * amp
    bob = 2.5 * amp * abs(math.sin(phase))
    hip = (0.0, -72.0 - bob)
    d = (math.sin(lean), -math.cos(lean))
    sh = (hip[0] + 38 * d[0], hip[1] + 38 * d[1])
    hd = (sh[0] + 22 * d[0] + 3, sh[1] + 22 * d[1])

    def leg(j):
        ph = phase + j * math.pi
        lift = max(0.0, math.cos(ph)) * amp
        a1 = A_leg * math.sin(ph) + 0.45 * climb * lift
        k = (0.5 + 1.0 * climb) * lift
        knee = (hip[0] + 36 * math.sin(a1), hip[1] + 36 * math.cos(a1))
        b1 = a1 - k
        foot = (knee[0] + 36 * math.sin(b1), knee[1] + 36 * math.cos(b1))
        return [hip, knee, foot, (foot[0] + 10, foot[1] + 1.5)]

    def arm(j, up=0.0):
        ph = phase + (j + 1) * math.pi
        a1 = A_arm * math.sin(ph) * (1 - up) + up * 2.0
        el = (sh[0] + 22 * math.sin(a1), sh[1] + 22 * math.cos(a1))
        b1 = a1 + 0.35 * (1 - up) + 0.25 * up
        hand = (el[0] + 20 * math.sin(b1), el[1] + 20 * math.cos(b1))
        return [sh, el, hand]

    ctx.save()                                         # 影
    ctx.scale(1, 0.22)
    ctx.arc(4, 0, 30, 0, 2 * math.pi)
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
    _limb(ctx, arm(0, reach), 12, col)
    ctx.restore()


# ---------- 絵: 建物の断面 ----------

def _line(ctx, x0, y0, x1, y1, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.move_to(x0, y0)
    ctx.line_to(x1, y1)
    ctx.stroke()


def draw_flight(ctx, xa, xb, y0, rise, front=True, up_right=True):
    """階段1本（y0 から rise 上がる）。up_right=True は左下→右上、False は右下→左上。front=False は奥の階段（うすく）"""
    n = 8
    al = 0.95 if front else 0.5
    if not up_right:
        xa, xb = xb, xa
    dx = (xb - xa) / n
    ctx.move_to(xa, y0)
    for i in range(n):
        y = y0 - rise * (i + 1) / n
        ctx.line_to(xa + dx * i, y)
        ctx.line_to(xa + dx * (i + 1), y)
    ctx.line_to(xb, y0 - rise + 16)
    ctx.line_to(xa, y0 + 16)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(SLAB if front else WALL, al))
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85 * al))
    ctx.set_line_width(2.4)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.6 * al))       # 手すり
    ctx.set_line_width(2.0)
    ctx.move_to(xa, y0 - 52)
    ctx.line_to(xb, y0 - rise - 52)
    ctx.stroke()


def draw_building(ctx, t, tau):
    n = sample()["p"]["n"]
    top = floor_y(n + 1)
    fill(ctx, hexrgb("#a8d68f", 0.35))                 # 地面
    ctx.rectangle(0, GROUND, W, SCENE_H - GROUND)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#8a6b4a", 0.45))
    ctx.set_line_width(2)
    for i in range(30):
        x = i * 40 + 10
        ctx.move_to(x, GROUND + 8)
        ctx.line_to(x - 12, GROUND + 20)
    ctx.stroke()
    fill(ctx, hexrgb("#fbf7ee", 0.92))                 # 建物の中
    ctx.rectangle(BX0, top, BX1 - BX0, GROUND - top)
    ctx.fill()
    fill(ctx, hexrgb(SHAFT, 0.95))                     # 昇降路
    ctx.rectangle(SH_X0, top, SH_X1 - SH_X0, GROUND - top)
    ctx.fill()
    for k in range(1, n):                              # 奥の階段（中の踊り場から左へ上る）
        draw_flight(ctx, FL_A, FL_B, floor_y(k) - FH / 2, FH / 2, front=False, up_right=False)
    for k in range(1, n):                              # 手前の階段（右へ上る）と中の踊り場
        y0 = floor_y(k)
        draw_flight(ctx, FL_A, FL_B, y0, FH / 2, front=True)
        fill(ctx, hexrgb(SLAB))
        ctx.rectangle(FL_B, y0 - FH / 2, LAND_R - FL_B, 14)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(2.4)
        ctx.stroke()
    for k in range(2, n + 2):                          # 床（階段室の踊り場と廊下。昇降路の中は床がない）
        y = floor_y(k)
        spans = ((BX0, FL_A), (ST_X1, SH_X0)) if k <= n else ((BX0, BX1),)
        for xa, xb in spans:
            fill(ctx, hexrgb(SLAB))
            ctx.rectangle(xa, y, xb - xa, 14)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.85))
            ctx.set_line_width(2.4)
            ctx.stroke()
    _line(ctx, BX0, GROUND, BX1, GROUND, 3.5)
    for k in range(1, n + 1):                          # 壁
        y = floor_y(k)
        _line(ctx, ST_X1, y - FH + 14, ST_X1, y - 96, 3.0)
        _line(ctx, SH_X0, y - FH + 14, SH_X0, y - DOOR_H - 4, 3.0)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45))     # 部屋のドア（廊下の奥）
        ctx.set_line_width(2)
        core.rrect(ctx, 530, y - 92, 46, 92, 3)
        ctx.stroke()
    _line(ctx, BX0, top, BX0, GROUND, 4.0)
    _line(ctx, BX1, top, BX1, GROUND, 4.0)
    _line(ctx, BX0 - 12, top, BX1 + 12, top, 5.0)     # 屋上
    y3 = floor_y(3)                                    # 3階のゴールの旗（階段の踊り場と、エレベーターの前）
    for fx in (BX0 + 18, 640.0):
        _line(ctx, fx, y3, fx, y3 - 70, 2.5)
        ctx.move_to(fx, y3 - 70)
        ctx.line_to(fx + 30, y3 - 61)
        ctx.line_to(fx, y3 - 52)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(RED, 0.9))
        ctx.fill()


def draw_elevator(ctx, t, tau):
    s = sample()
    n = s["p"]["n"]
    pos, mv, doors = car_state(tau)
    cy = GROUND - (pos - 1) * FH                       # かごの床
    top = floor_y(n + 1)
    cw_y = GROUND - 80 - (n - pos) / max(1, n - 1) * (GROUND - 80 - top - 40)   # おもり（かごと逆に動く）
    ctx.set_source_rgba(*hexrgb(INK, 0.6))
    ctx.set_line_width(2)
    ctx.move_to((CAR_X0 + CAR_X1) / 2, top + 14)
    ctx.line_to((CAR_X0 + CAR_X1) / 2, cy - CAR_H)
    ctx.move_to(951, top + 22)
    ctx.line_to(951, cw_y)
    ctx.stroke()
    ctx.arc(940, top + 24, 12, 0, 2 * math.pi)
    ctx.stroke()
    fill(ctx, hexrgb("#9aa3b5", 0.9))
    ctx.rectangle(941, cw_y, 20, 70)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.stroke()
    fill(ctx, hexrgb(CAR))                             # かご
    ctx.rectangle(CAR_X0, cy - CAR_H, CAR_X1 - CAR_X0, CAR_H)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3.2)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb("#ffd84d", 0.8))       # かごの照明
    ctx.set_line_width(4)
    ctx.move_to(CAR_X0 + 40, cy - CAR_H + 8)
    ctx.line_to(CAR_X1 - 40, cy - CAR_H + 8)
    ctx.stroke()
    for k in range(1, n + 1):                          # 各階の乗り場のドア（開くと上へ引っこむ）・階の表示・ボタン
        y = floor_y(k)
        o = doors.get(k, 0.0)
        hgt = DOOR_H * (1 - o)
        if hgt > 1:
            fill(ctx, hexrgb("#b9c3d3", 0.95))
            ctx.rectangle(SH_X0 - 7, y - DOOR_H, 14, hgt)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.85))
            ctx.set_line_width(2.2)
            ctx.stroke()
        if o > 0.05:
            ctx.set_source_rgba(*hexrgb(INK, 0.4))
            ctx.set_dash([5, 5])
            ctx.set_line_width(1.8)
            ctx.rectangle(SH_X0 - 7, y - DOOR_H, 14, DOOR_H)
            ctx.stroke()
            ctx.set_dash([])
        fill(ctx, (1, 1, 1, 0.95))
        core.rrect(ctx, 700, y - FH + 20, 62, 38, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(2)
        ctx.stroke()
        fill(ctx, (1, 1, 1, 0.95))
        core.rrect(ctx, BTN_X - 8, y - 72, 16, 24, 4)
        ctx.fill_preserve()
        ctx.stroke()
    b = s["e"]["board"]                                # 1階のボタンのランプ（押してから、ドアが開くまで）
    if 0.6 <= tau < b["open0"]:
        fill(ctx, hexrgb("#ff9f2e"))
        ctx.arc(BTN_X, floor_y(1) - 60, 5.5, 0, 2 * math.pi)
        ctx.fill()


def draw_scene_text(ctx, t, tau):
    """場面の字: 階の名前・階の表示"""
    n = sample()["p"]["n"]
    pos, mv, _ = car_state(tau)
    cf = int(round(pos))
    arrow = "▲" if mv > 0 else ("▼" if mv < 0 else "")
    for k in range(1, n + 1):
        y = floor_y(k)
        stext(ctx, t, f"{k}階", 108, y - FH / 2, 34, RED if k == 3 else INK)
        stext(ctx, t, f"{cf}{arrow}", 731, y - FH + 39, 30, RED)
    xd, yd = to_dev(t, 108, floor_y(3) - FH / 2)
    r = 34 * scene_scale(t)
    bx, by, bw, bh = scene_box(t)
    if xd - r * 1.2 > 60 and yd - r > by:
        note.pen_circle(ctx, xd, yd, r * 1.25, r * 0.9, RED, seed=9, width=3.5)


def scene_alpha(t):
    if t < T_G0:
        return 1.0
    return 1 - ease((t - T_G0) / 0.4)


def draw_scene(ctx, t):
    a = scene_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    ctx.push_group()
    ctx.save()
    bx, by, bw, bh = scene_box(t)
    ctx.rectangle(bx, by, bw, bh)
    ctx.clip()
    ctx.save()
    apply_scene(ctx, t)
    draw_building(ctx, t, tau)
    draw_elevator(ctx, t, tau)
    sa = stair_state(tau)
    draw_person(ctx, sa["x"], sa["y"], P_H, COL_A, 2 * math.pi * 1.0 * t if sa["walk"] else 0.0,
                amp=1.0 if sa["walk"] else 0.0, face=sa["face"], climb=0.0 if sa["done"] else 1.0)
    sb = elev_state(tau)
    sway = 0.0 if sb["walk"] else 0.3 * math.sin(2 * math.pi * 0.5 * t)
    draw_person(ctx, sb["x"], sb["y"], P_H, COL_B, 2 * math.pi * 1.0 * t if sb["walk"] else sway,
                amp=1.0 if sb["walk"] else 0.2, face=sb["face"], reach=sb["reach"])
    ctx.restore()
    ctx.restore()
    ctx.save()
    draw_scene_text(ctx, t, tau)
    for st, k in ((sa, "a"), (sb, "b")):              # 頭の上に A・B の丸
        xd, yd = to_dev(t, st["x"], st["y"] - P_H - 24)
        r = 18 * scene_scale(t)
        if yd - r < by + 2:
            continue
        fill(ctx, (1, 1, 1, 0.92))
        ctx.arc(xd, yd, r, 0, 2 * math.pi)
        ctx.fill()
        note.pen_circle(ctx, xd, yd, r, r, INKC[k], seed=13 + (k == "b"), width=3.2)
        text(ctx, TAG[k], xd, yd, max(24.0, 28 * scene_scale(t)), INKC[k])
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)


# ---------- 読み取り ----------

def readout_alpha(t):
    if T_GO - 0.1 <= t < T_G0:
        return ease_out((t - T_GO + 0.1) / 0.4) * (1 - ease((t - T_G0) / 0.35))
    return 0.0


STATUS = {"wait": "かごを待つ", "board": "乗りこむ", "ride": "上がっている", "door": "ドアの開け閉め", "out": "降りる",
          "done": "着いた！"}


def draw_readouts(ctx, t):
    a = readout_alpha(t)
    if a <= 0:
        return
    tau = tau_of(t)
    s = sample()
    sa, sb = stair_state(tau), elev_state(tau)
    pos, mv, _ = car_state(tau)
    text(ctx, f"再生 {speed_now(t):.1f}倍" if speed_now(t) < 1.95 else f"再生 {speed_now(t):.0f}倍", 160, 1168, 24,
         PENCIL, bold=False, align="left", alpha=a)
    cols = (("a", 330.0, sa, s["t_st"]), ("b", 780.0, sb, s["t_el"]))
    for k, cx, st, t_fin in cols:
        text(ctx, f"{TAG[k]} {NAME[k]}", cx, 1205, 34, INKC[k], alpha=a)
        fl = int(math.floor(1 + st["h"] + 1e-6)) if k == "a" else st["fl"]
        text(ctx, f"{min(fl, 3)}階", cx, 1262, 54, INK, alpha=a)
        if k == "a":
            stat = "着いた！" if st["done"] else "のぼっている"
        else:
            stat = STATUS[st["status"]]
            if st["status"] == "wait":
                stat = f"かごを待つ（{int(round(pos))}階）"
        text(ctx, stat, cx, 1318, 30, RED if st["done"] else PENCIL, bold=st["done"], alpha=a)
        if st["done"]:
            u = clamp01((t - t_of(t_fin)) / 0.35)
            text(ctx, f"{t_fin:.1f}秒", cx, 1385, 48, INKC[k], alpha=a)
            note.pen_circle(ctx, cx, 1385, 110, 38, RED, seed=70 + (k == "b"), width=5, progress=u, alpha=a)
        else:
            text(ctx, f"{tau:.1f}秒", cx, 1385, 48, INK, alpha=a)
    if t >= T_FIN2:
        b = a * ease_out((t - T_FIN2 - 0.2) / 0.3)
        w = "a" if s["t_st"] < s["t_el"] else "b"
        dd = abs(s["t_st"] - s["t_el"])
        note.sticky(ctx, f"{NAME[w]}が\n{dd:.1f}秒 早く着いた", 580, 840, 44, "yellow", a=b, tilt=-0.02)


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
    r = results()
    win_b = (r["el_u"] < r["st_u"]).astype(int)
    cols = np.zeros((G_ROWS, G_COLS, 4), np.uint8)
    pal = np.array([bgra(COL_A), bgra(COL_B)], np.uint8)
    m = min(N_TRIAL, key * G_COLS)
    flat = cols.reshape(-1, 4)
    flat[:m] = pal[win_b[:m]]
    surf, keep = grid_image(cols, cell=G_CELL, gap_color=(0, 0, 0, 0), gap=1)
    _GRID[key] = (surf, keep)
    return _GRID[key]


def grid_alpha(t):
    if t < T_G0:
        return 0.0
    return ease((t - T_G0) / 0.35) * (1 - ease((t - T_WHY) / 0.35))


def fmt(n):
    return f"{int(round(n)):,}"


def pct_i(p):
    return f"{int(math.floor(p * 100 + 0.5))}%"


def draw_grid(ctx, t):
    a = grid_alpha(t)
    if a <= 0:
        return
    r = results()
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
    win_b = r["el_u"][:m] < r["st_u"][:m]
    for i, (lab, cnt, col) in enumerate(((f"A {NAME['a']}が先に着いた", int(m - win_b.sum()), COL_A),
                                         (f"C {NAME['b']}が先に着いた", int(win_b.sum()), COL_B))):
        y = 1180 + i * 58
        fill(ctx, hexrgb(col, a))
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.7 * a))
        ctx.set_line_width(2)
        ctx.rectangle(200, y - 17, 34, 34)
        ctx.stroke()
        text(ctx, lab, 250, y, 34, INK, align="left", alpha=a)
        text(ctx, f"{fmt(cnt)}回", 915, y, 34, INK, align="right", alpha=a)
    text(ctx, "1マス＝1回。先に3階に着いた人の色", 580, 1294, 26, PENCIL, bold=False, alpha=a)
    if t >= T_REV:
        sh = shown()
        b = ease_out((t - T_REV - 0.3) / 0.3) * a
        note.sticky(ctx, f"階段が先は 約{pct_i(sh['p_up'])}。差は 真ん中で 約{sh['gap_med']:.0f}秒", 580, 1378,
                    34, "pink", fg=RED, a=b, tilt=-0.015)


# ---------- なぜ: かごがどこにいたか ----------
WHY_ROWS = ("1階で 止まっていた", "ほかの階で 止まっていた", "ほかの人を 運んでいた")
BAR_STEP = 0.45


def why_alpha(t):
    if t < T_WHY:
        return 0.0
    return ease_out((t - T_WHY) / 0.3) * (1 - ease((t - T_TW) / 0.35))


def bars(ctx, t, t0, rows, ys, a, x0=300.0, ln=480.0):
    """横の棒（0〜100%・同じ目盛り）。rows = [(ラベル, 値, 色)]"""
    yt, yb = ys[0] - 40, ys[-1] + 40
    ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
    ctx.set_line_width(3)
    ctx.set_dash([9, 8])
    ctx.move_to(x0 + ln / 2, yt)
    ctx.line_to(x0 + ln / 2, yb)
    ctx.stroke()
    ctx.set_dash([])
    text(ctx, "半々", x0 + ln / 2, yb + 26, 28, RED, alpha=a)
    for i, ((lab, val, col), y) in enumerate(zip(rows, ys)):
        tk = t0 + 0.3 + i * BAR_STEP
        if t < tk:
            break
        g = ease_out((t - tk) / 0.45)
        text(ctx, lab, x0, y - 52, 34, INK, align="left", alpha=a)
        ctx.set_source_rgba(*hexrgb(INK, 0.35 * a))
        ctx.set_line_width(2)
        ctx.rectangle(x0, y - 22, ln, 44)
        ctx.stroke()
        w = ln * val * g
        if w > 1:
            ctx.set_source_rgba(*hexrgb(col, 0.95 * a))
            core.rrect(ctx, x0, y - 22, w, 44, 6)
            ctx.fill_preserve()
            ctx.set_source_rgba(*hexrgb(INK, 0.8 * a))
            ctx.set_line_width(2.5)
            ctx.stroke()
        text(ctx, pct_i(val), x0 + ln + 16, y, 38, INK, align="left", alpha=a * clamp01(g * 3 - 2))


def draw_why(ctx, t):
    a = why_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "ボタンを押したとき、かごは どこにいた？", 580, 650, 40, INK, alpha=a)
    text(ctx, "棒は「階段の人が先に着いた」割合", 580, 704, 28, PENCIL, bold=False, alpha=a)
    rows = [(lab, sh["by_scen"][k][0], COL_A) for k, lab in enumerate(WHY_ROWS)]
    bars(ctx, t, T_WHY, rows, (830.0, 970.0, 1110.0), a)
    tb = T_WHY + 0.3 + len(rows) * BAR_STEP + 0.5
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, "1階にいれば エレベーター。\nいなければ たいてい階段", 580, 1290, 38, "yellow", a=b, tilt=-0.02)


# ---------- ひねり: 下りなら？ ----------
TW_STEP = BAR_STEP


def tw_alpha(t):
    if t < T_TW_RUN:
        return 0.0
    return ease_out((t - T_TW_RUN) / 0.3) * (1 - ease((t - T_Q) / 0.35))


def tw_done_t():
    return T_TW_RUN + 0.3 + 2 * TW_STEP + 0.5


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    sh = shown()
    text(ctx, "階段の人が 先に着いた割合（1万回ずつ）", 580, 650, 40, INK, alpha=a)
    text(ctx, "同じ建物・同じ人・同じかごの場所で、行き先だけ逆に", 580, 704, 28, PENCIL, bold=False, alpha=a)
    rows = [("上り 1階 → 3階", sh["p_up"], COL_A), ("下り 3階 → 1階", sh["p_down"], COL_D)]
    bars(ctx, t, T_TW_RUN, rows, (850.0, 1000.0), a)
    tb = tw_done_t()
    if t >= tb:
        b = ease_out((t - tb) / 0.3) * a
        note.sticky(ctx, f"下りは、差が 真ん中で 約{sh['gap_d_med']:.0f}秒", 580, 1170, 34, "pink", fg=RED, a=b, tilt=-0.02)
    if t >= tb + 1.0:
        b = ease_out((t - tb - 1.0) / 0.3) * a
        text(ctx, "階段は 下りが速い。エレベーターは 同じ", 580, 1285, 30, INK, bold=False, alpha=b)


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


CD_X, CD_Y = 330.0, 950.0


class KIntro(note.Intro):
    """この回だけの冒頭。上: 問い2行・前提・三択（横1列）。その下いっぱいに、建物の断面（0秒目から2人が動いている）"""
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
            text(ctx, DETAIL, 580, 568, 34, INK, bold=False, alpha=a1)
        for i, (v, x0, vs) in enumerate(choice_row(self.labels, 40, 575, 820)):
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


INTRO = KIntro(BIG_Q, LABELS, correct=CORRECT, msg="", rule=None)


# ---------- 本体 ----------

def body(ctx, t):
    draw_scene(ctx, t)
    draw_readouts(ctx, t)
    if T_GO - 0.1 <= t < T_GO + 1.4:
        b = ease_out((t - T_GO + 0.1) / 0.3) * (1 - ease((t - T_GO - 1.0) / 0.4))
        note.sticky(ctx, "3階に着くまで", 640, 700, 34, "yellow", a=b, tilt=-0.03)
    draw_grid(ctx, t)
    draw_why(ctx, t)
    if T_TW <= t < T_TW_RUN:                          # ひねり
        ba = ease_out((t - T_TW) / 0.25) * (1 - ease((t - T_TW_RUN + 0.25) / 0.25))
        note.banner(ctx, "では、下りなら？", 580, 860, a=ba, t_rel=t - T_TW, size=60)
    draw_twist(ctx, t)
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0   # 締め（答えは出さない）
    if q > 0:
        note.sticky(ctx, "あなたは、\n何階からエレベーター？", 580, 860, 56, "yellow", a=q, tilt=-0.02)
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

def hum(dur, f=82.0):
    tt = np.arange(int(SR * dur)) / SR
    env = np.minimum(1, tt / 0.3) * np.minimum(1, (dur - tt) / 0.3)
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * 2 * f * tt)) * env * 0.5


def build_audio():
    s = sample()
    e = s["e"]
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(130.8, 196.0, 261.6, 329.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    mx.add(t_of(0.5), blip(1568.0, 0.08), 0.35)        # ボタン
    tt = 0.12                                          # 階段の足音（足の動きと同じ周期。速い再生の間は鳴らさない）
    while tt < T_G0:
        tau = tau_of(tt)
        if tau < s["t_st"] and speed_now(tt) < 2.2:
            mx.add(tt, thump(0.12) * 0.5 + np.pad(tick(900.0, 0.02), (0, int(SR * 0.1))), 0.10)
        tt += 0.5
    for ev in e["log"]:                                # かごが動く音・ドアのチャイム
        if ev[0] == "move":
            a0, a1 = t_of(ev[1]), t_of(ev[2])
            if a1 > a0 + 0.2:
                mx.add(a0, hum(a1 - a0), 0.12)
        if ev[0] == "stop" and ev[3] in (1, 3):
            mx.add(t_of(ev[1]), bell(1318.5, 0.9), 0.25)
    mx.add(T_GO - 0.6, riser(0.8), 0.4)
    beat(mx, T_GO, T_FIN1 - 1.2, bpm=124, vol=0.32)
    mx.add(t_of(s["t_st"]), bell(784.0, 1.2), 0.45)
    mx.add(t_of(s["t_el"]), bell(659.3, 1.2), 0.45)
    mx.add(T_G0 - 0.5, riser(0.7), 0.4)               # 1万回
    beat(mx, T_G0 + 0.2, T_G1, bpm=128, vol=0.45)
    mx.add(T_G1, thump(), 0.5)
    mx.add(T_REV, bell(784.0, 1.6), 0.55)
    for i in range(3):                                 # なぜ
        mx.add(T_WHY + 0.3 + i * BAR_STEP, blip(523.3 + 90 * i, 0.12), 0.3)
    mx.add(T_TW, riser(0.8), 0.45)                    # ひねり
    for i in range(2):
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
    # (1) 台形の移動: 長い距離は d/v + v/a、短い距離は 2√(d/a)。flight_pos は最後に d に着く
    checks.append(("移動の時間（長い距離）", flight(10.0, 1.0, 0.8), 10.0 / 1.0 + 1.0 / 0.8, 1e-9))
    checks.append(("移動の時間（短い距離）", flight(0.5, 1.5, 0.6), 2 * math.sqrt(0.5 / 0.6), 1e-9))
    checks.append(("移動の位置（着いたとき）", flight_pos(flight(7.0, 1.2, 0.9), 7.0, 1.2, 0.9), 7.0, 1e-9))
    checks.append(("移動の位置（真ん中で半分）", flight_pos(flight(7.0, 1.2, 0.9) / 2, 7.0, 1.2, 0.9), 3.5, 1e-9))
    # (2) 1階で止まっていた回（S1）で2階に止まらない回は、式どおり: 開く+乗る+待つ+閉まる+動き出し+移動+開く+降りる
    params = all_params(SEED_MAIN, 3000)
    worst = 0.0
    for i, p in enumerate(params):
        if p["scen"] != 0 or p["ride2"]:
            continue
        f = p["t_open"] + T_IN + p["dwell"] + p["t_close"] + p["start"] + flight(2 * p["hf"], p["v"], p["acc"]) \
            + p["t_open"] + T_OUT
        worst = max(worst, abs(f - r["el_u"][i]))
    checks.append(("1階で止まっていた回のエレベーターの時間 − 式（最大・秒）", worst, 0.0, 1e-9))
    checks.append(("1階で止まっていた回は 待ち0秒", float(np.abs(r["wait_u"][r["scen"] == 0]).max()), 0.0, 1e-9))
    # (3) 階段の速さの真ん中が 0.24 m/秒（エスカレーターのロングの 0.2〜0.25 の間）
    checks.append(("階段の速さの真ん中（m/秒）", float(np.median(r["v_up"])), STAIR_MED, 0.005))
    checks.append(("下り÷上りの真ん中（告示の 36/27 ≒ 1.33 の近く）", float(np.median(r["v_down"] / r["v_up"])), 36 / 27, 0.02))
    # (4) 答え: 決めておいた規則で計算結果から出した答えが、画面の答えと同じ
    checks.append(("画面の答えが、規則で出した答えと同じ", float(answer_by_rule(sh["p_up"], sh["gap_med"])),
                   float(INTRO.correct), 0.0))
    # (5) 見本は1万回の中の1回で、結果の向きが多数派と同じ・差が真ん中の値の近く
    smp = sample()
    checks.append(("見本の差（秒）が真ん中の値の近く", smp["gap"], sh["gap_med"], 1.0))
    # (6) 画面の回数が足して1万（同時は無い）
    checks.append(("先に着いた回の合計", float(sh["n_st"] + sh["n_el"]), float(N_TRIAL), 0.0))
    # (7) 下り: 階段が先が上りより多い（画面の向き）
    checks.append(("下りのほうが 階段が先に着く割合が高い", float(sh["p_down"] > sh["p_up"]), 1.0, 0.0))
    check_answers(checks)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    setup()
    report()
    s = sample()
    print(f"長さ {DURATION:.1f}秒  再生 {RACE_X:.2f}倍  着く {T_FIN1:.2f} / {T_FIN2:.2f}秒  答え {T_REV:.1f}  なぜ {T_WHY:.1f}  "
          f"ひねり {T_TW:.1f}  締め {T_Q:.1f}  見本 {s['i']}（階段 {s['t_st']:.1f}秒 / エレベーター {s['t_el']:.1f}秒）")
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.5, 1.0, 2.5, 5.0, 8.0, 8.6, 10.0, 12.0, 14.0, 16.0, 18.0, T_FIN1 - 0.3, T_FIN2 + 0.8,
              T_G0 + 1.5, T_G1 + 0.3, T_REV + 2.0, T_WHY + 3.0, T_TW + 1.0, T_TW_RUN + 2.5, T_Q + 1.5,
              DURATION - 0.2]
        stills(draw, ts, OUT)
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
