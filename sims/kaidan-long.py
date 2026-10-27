"""何階まで、階段が早い？（横型ロング）— 2026-10-19 作成（モデル部分。描画・場面は後で足す）

構成案: research/longform_next_2026-10-28.md（A 階段とエレベーター。統括経由でユーザー OK）
元のショート: sims/kaidan-elevator.py（触らない。建物・階段・エレベーターのモデルと数値はそこからコピーし、行き先の階を伸ばした）

コピーした決めごと（ショートと同じ）
  建物: 1階ぶんの高さ 3.0〜4.0m。エレベーター1台
  階段: 高さ方向の速さ 真ん中 0.24 m/秒（対数正規・ばらつき 0.20・0.14〜0.40 で切る。Ronchi ほか 2015）。
        エスカレーターのロング（10/21）は 0.2 / 0.25 m/秒 で比べた。真ん中 0.24 はその間。下りは上りの 1.20〜1.45倍（告示1441号の比 ≒1.33）。
        何階ぶん上っても同じ速さとする（疲れは入れない）
  エレベーター: 定格 45〜90 m/分・加速度 0.6〜1.0 m/秒²・動き出し 0.5〜1.0秒・ドア 開1.5〜3.0／閉2.0〜3.5秒・
        乗る1.2秒/人・降りる1.0秒/人・閉まるまでの間 1.0〜2.5秒（Powell 2008 ほか）
  ボタンを押したときのかご: 1階で停止 30% ／ ほかの階で停止 30% ／ ほかの人を運んでいる 40%（ショートと同じ重み）
このロングで変えた・足した所
  行き先 D: 2〜10階。建物の階数は max(5, D)〜max(8, D+3)（D=3 ならショートと同じ 5〜8階建て）
  乗っている間の途中の階: 各階 10% で止まる（ショートは「2階に 10%」。D=3 では同じ）
  ほかの人に呼ばれる階の記録を 14階ぶんに伸ばした
  3章「かごの場所を見て決める」: ボタンの上の表示で、かごが1階にいればエレベーター、いなければ階段
  4章「朝の混雑」（仮定）: かごが運転中 80%・1階で停止 10%・ほかの階で停止 10%、途中の階で呼ばれる 30%、乗っている間の途中の階 30%、
        1階で降りる人 2〜6人
  5章「下り」: D階 → 1階。同じ建物・同じ人・同じかごの状態で、D階で下りのボタンを押す

使い方
  python -X utf8 sims/kaidan-long.py --numbers    照合 → out/kaidan-long/numbers.md・data.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.core import check_answers

SLUG = "kaidan-long"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---------- ショート sims/kaidan-elevator.py と同じ値 ----------
FLOOR_H = (3.0, 4.0)
STAIR_MED, STAIR_SIG, STAIR_CLIP = 0.24, 0.20, (0.14, 0.40)
DOWN_RATIO = (1.20, 1.45)
SPEED = (45.0, 90.0)
ACC = (0.6, 1.0)
START = (0.5, 1.0)
T_OPEN = (1.5, 3.0)
T_CLOSE = (2.0, 3.5)
T_IN, T_OUT = 1.2, 1.0
DWELL = (1.0, 2.5)
RESID = (0.0, 4.0)
P_MID_DOWN = 0.30
SHORT_P3, SHORT_GAP3 = 0.597, 4.2                   # ショートの概要欄（3階・1万回）: 階段が先 59.7%・差の真ん中 4.2秒
SHORT_P3_DOWN = 0.888                               # ショートの下り（3階→1階）: 階段が先 88.8%
# ---------- このロングの値 ----------
N = 10000
DESTS = list(range(2, 11))                          # 行き先 2〜10階
NORMAL = dict(scen=(0.30, 0.30, 0.40), hall=0.10, ride=0.10, n_exit=(1, 3))
RUSH = dict(scen=(0.10, 0.10, 0.80), hall=0.30, ride=0.30, n_exit=(2, 6))
NH = 14
SEED_MAIN, SEED_AGAIN = 20261028, 520261028


def draw_trial(rng, D, mode=NORMAL):
    u = lambda lo_hi: float(rng.uniform(lo_hi[0], lo_hi[1]))   # noqa: E731
    lo, hi = max(5, D), max(8, D + 3)
    n = int(rng.integers(lo, hi + 1))
    v_up = float(np.clip(STAIR_MED * math.exp(rng.normal(0, STAIR_SIG)), *STAIR_CLIP))
    p = dict(n=n, hf=u(FLOOR_H), v_up=v_up, v_down=v_up * u(DOWN_RATIO),
             v=u(SPEED) / 60.0, acc=u(ACC), start=u(START), t_open=u(T_OPEN), t_close=u(T_CLOSE), dwell=u(DWELL))
    s = int(rng.choice(3, p=mode["scen"]))
    p["scen"] = s
    p["resid"] = u(RESID)
    p["hall"] = rng.uniform(0, 1, NH) < mode["hall"]
    p["ride_mid"] = rng.uniform(0, 1, NH) < mode["ride"]
    p["n_exit"] = int(rng.integers(mode["n_exit"][0], mode["n_exit"][1] + 1))
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
    if d <= 0:
        return 0.0
    if d >= v * v / a:
        return d / v + v / a
    return 2 * math.sqrt(d / a)


class Car:
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
    """ショートの elevator と同じ手順。違いは「乗っている間の途中の階」を各階 ride_mid で決める所だけ"""
    s, f0, d = p["scen"], p["f0"], p["dir"]
    car = Car(p, f0)
    carried = []
    n_exit = 0
    going_down = dest < origin
    if s == 2:
        car.wait(p["resid"])
        if d == 1:
            stops = p["stops"]
            for k, fl in enumerate(stops):
                car.move(fl)
                if fl == origin and k == len(stops) - 1 and going_down:
                    n_exit = 1
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
                            n_exit += 1
                car.move(origin)
        else:
            stops = p["stops"]
            if going_down and f0 > origin:
                for fl in range(f0 - 1, origin, -1):
                    if fl in stops or p["hall"][fl]:
                        car.move(fl)
                        car.stop(1 if fl in stops else 0, 0 if fl in stops else 1)
                car.move(origin)
                carried = [fl for fl in stops if fl < origin] + [fl for fl in range(origin - 1, 1, -1) if p["hall"][fl]]
                n_exit = 1 if origin in stops else 0
            else:
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
        car.move(origin)
    board = car.stop(n_exit, 1)
    t_wait = board["open0"]
    if going_down:
        ride_stops = {fl for fl in carried if fl not in (origin, dest)} | {fl for fl in range(dest + 1, origin) if p["ride_mid"][fl]}
    else:
        ride_stops = {fl for fl in range(origin + 1, dest) if p["ride_mid"][fl]}
    rng_dir = range(origin + 1, dest) if dest > origin else range(origin - 1, dest, -1)
    for fl in rng_dir:
        if fl in ride_stops:
            car.move(fl)
            car.stop(1, 0)
    car.move(dest)
    out = car.stop(1, 0, mine=True)
    return dict(t=out["out"], wait=t_wait, log=car.log)


def stairs(p, origin, dest):
    h = abs(dest - origin) * p["hf"]
    v = p["v_up"] if dest > origin else p["v_down"]
    return h / v


def run(seed, D, mode=NORMAL, n=N):
    """行き先 D 階。上り（1→D）と下り（D→1）。返り値は1回ごとの配列"""
    rng = np.random.default_rng(seed + D * 1000)
    st_u, el_u, st_d, el_d, scen, wait_u = (np.zeros(n) for _ in range(6))
    for i in range(n):
        p = draw_trial(rng, D, mode)
        eu, ed = elevator(p, 1, D), elevator(p, D, 1)
        st_u[i], el_u[i], st_d[i], el_d[i] = stairs(p, 1, D), eu["t"], stairs(p, D, 1), ed["t"]
        scen[i], wait_u[i] = p["scen"], eu["wait"]
    return dict(st_u=st_u, el_u=el_u, st_d=st_d, el_d=el_d, scen=scen, wait_u=wait_u)


def summarize(r):
    up_st = r["st_u"] < r["el_u"]
    dn_st = r["st_d"] < r["el_d"]
    look = np.where(r["scen"] == 0, r["el_u"], r["st_u"])         # かごが1階にいればエレベーター、いなければ階段
    best = np.minimum(r["st_u"], r["el_u"])
    return dict(p_up=float(up_st.mean()), gap_up=float(np.median(r["el_u"] - r["st_u"])),
                med_st_u=float(np.median(r["st_u"])), med_el_u=float(np.median(r["el_u"])),
                p_down=float(dn_st.mean()), gap_down=float(np.median(r["el_d"] - r["st_d"])),
                p_up_s1=float(up_st[r["scen"] == 0].mean()), p_up_s23=float(up_st[r["scen"] != 0].mean()),
                mean_st=float(r["st_u"].mean()), mean_el=float(r["el_u"].mean()), mean_look=float(look.mean()),
                mean_best=float(best.mean()), p_look_right=float(np.mean(np.isclose(look, best))),
                wait_mean=float(r["wait_u"].mean()))


def crossover(ps, ds=DESTS, level=0.5):
    """階段が先の割合 ps（行き先ごと）が level を切る行き先（直線でつないだ値）。切らなければ nan"""
    ps = np.asarray(ps)
    for k in range(1, len(ps)):
        if ps[k - 1] >= level > ps[k]:
            return float(ds[k - 1] + (ps[k - 1] - level) / (ps[k - 1] - ps[k]) * (ds[k] - ds[k - 1]))
    return float("nan")


def compute():
    R = {"normal": {}, "normal_again": {}, "rush": {}}
    for D in DESTS:
        R["normal"][D] = summarize(run(SEED_MAIN, D))
        R["normal_again"][D] = summarize(run(SEED_AGAIN, D))
        R["rush"][D] = summarize(run(SEED_MAIN + 7, D, RUSH))
    for k in ("normal", "normal_again", "rush"):
        R[f"top_up_{k}"] = max(D for D in DESTS if R[k][D]["p_up"] >= 0.5)        # 分かれ目（台本の定義）: 階段が先の回のほうが多い、いちばん上の階
        R[f"top_down_{k}"] = max(D for D in DESTS if R[k][D]["p_down"] >= 0.5)
        R[f"cross_up_{k}"] = crossover([R[k][D]["p_up"] for D in DESTS])
        R[f"cross_down_{k}"] = crossover([R[k][D]["p_down"] for D in DESTS])
    R["samples"] = pick_samples()
    return R


def _plain(p):
    return {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in p.items()}


def pick_samples(seed=SEED_MAIN):
    """絵のための1回ぶん。p（建物・人・かごの値）と、かごの記録（log）・階段の時間を残す"""
    out = {}
    want = [
        ("open3", 3, NORMAL, lambda p, st, el: p["scen"] == 1 and p["f0"] >= 4 and 3.0 < el - st < 12.0),      # 冒頭: かごが上の階に止まっていて、階段が先
        ("look4_car1", 4, NORMAL, lambda p, st, el: p["scen"] == 0 and st - el > 5.0),                       # 3章: かごが1階 → エレベーターが先
        ("rush6", 6, RUSH, lambda p, st, el: p["scen"] == 2 and 3.0 < el - st < 20.0),                        # 4章: 混雑で、6階でも階段が先
    ]
    for name, D, mode, ok in want:
        rng = np.random.default_rng(seed + 99 + D)
        for i in range(5000):
            p = draw_trial(rng, D, mode)
            st, e = stairs(p, 1, D), elevator(p, 1, D)
            if ok(p, st, e["t"]):
                out[name] = dict(dest=D, trial=i, p=_plain(p), stairs=st, el_t=e["t"], el_wait=e["wait"], log=e["log"])
                break
    return out


def run_checks(R):
    c = []
    n3 = R["normal"][3]
    se = math.sqrt(0.25 / N)
    c += [
        ("1章: 3階は ショートの 59.7%（階段が先）と 4σ 以内", n3["p_up"], SHORT_P3, 4 * se + 0.005),
        ("1章: 3階の差の真ん中は ショートの 4.2秒と 1秒以内", n3["gap_up"], SHORT_GAP3, 1.0),
        ("5章: 3階の下りは ショートの 88.8% と 4σ 以内", n3["p_down"], SHORT_P3_DOWN, 4 * math.sqrt(0.1 / N) + 0.005),
    ]
    pu = [R["normal"][D]["p_up"] for D in DESTS]
    pd = [R["normal"][D]["p_down"] for D in DESTS]
    pr = [R["rush"][D]["p_up"] for D in DESTS]
    c += [
        ("2章: 行き先が上の階ほど、階段が先の割合は下がる（2〜10階）", float(all(a > b for a, b in zip(pu, pu[1:]))), 1.0, 0.0),
        ("2章: 分かれ目（半々）の階がある（2〜10階のあいだ）", float(not math.isnan(R["cross_up_normal"])), 1.0, 0.0),
        ("2章: 別の乱数でも、分かれ目は 0.3階 以内", R["cross_up_normal_again"], R["cross_up_normal"], 0.3),
        ("2章: かごが1階にいた回は、3階から上ではどこでも エレベーターが先のほうが多い（2階は階段が先 7割以上）",
         float(all(R["normal"][D]["p_up_s1"] < 0.5 for D in DESTS if D >= 3) and R["normal"][2]["p_up_s1"] > 0.7), 1.0, 0.0),
        ("3章: 分かれ目に近い 3階・4階では、表示を見て決めると いつも階段・いつもエレベーターより 平均が短い",
         float(all(R["normal"][D]["mean_look"] < min(R["normal"][D]["mean_st"], R["normal"][D]["mean_el"]) for D in (3, 4))), 1.0, 0.0),
        ("3章: 5階から上は、いつもエレベーターのほうが 表示を見て決めるより 平均が短い（迷わずエレベーター）",
         float(all(R["normal"][D]["mean_el"] < R["normal"][D]["mean_look"] for D in DESTS if D >= 5)), 1.0, 0.0),
        ("3章: 2階は、いつも階段が いちばん短い（表示を見ても得をしない）",
         float(R["normal"][2]["mean_st"] < min(R["normal"][2]["mean_look"], R["normal"][2]["mean_el"])), 1.0, 0.0),
        ("2章: 分かれ目は 3階と4階のあいだ（3.0〜4.0）", float(3.0 < R["cross_up_normal"] < 4.0), 1.0, 0.0),
        ("4章: 朝の混雑の分かれ目は 6〜8階", float(6.0 < R["cross_up_rush"] < 8.0), 1.0, 0.0),
        ("5章: 下りの分かれ目は 5〜6階", float(5.0 < R["cross_down_normal"] < 6.0), 1.0, 0.0),
        ("台本の分かれ目（階段が先の回のほうが多い、いちばん上の階）: ふだん3階・朝の混雑7階・下り5階・別の乱数でも3階",
         float((R["top_up_normal"], R["top_up_rush"], R["top_down_normal"], R["top_up_normal_again"]) == (3, 7, 5, 3)), 1.0, 0.0),
        ("台本の分かれ目は、2〜10階で 階段が先の割合が上から下へ1回だけ 50% をまたぐ（ふだん・混雑・下り）",
         float(all(sum((R[k][D][f] >= 0.5) != (R[k][D + 1][f] >= 0.5) for D in DESTS[:-1]) == 1 for k, f in (("normal", "p_up"), ("rush", "p_up"), ("normal", "p_down")))), 1.0, 0.0),
        ("4章: 朝の混雑では、どの階でも 階段が先の割合が ふだんより高い", float(all(a < b for a, b in zip(pu, pr))), 1.0, 0.0),
        ("4章: 朝の混雑の分かれ目は ふだんより上の階（または10階までに半々にならない）",
         float(math.isnan(R["cross_up_rush"]) or R["cross_up_rush"] > R["cross_up_normal"]), 1.0, 0.0),
        ("5章: 下りは、どの階でも 上りより階段が先の割合が高い", float(all(a < b for a, b in zip(pu, pd))), 1.0, 0.0),
    ]
    # 別の実装: 階段の時間は 高さ ÷ 速さ（閉じた式）。真ん中の値は 2階ぶん（3.5m平均）÷ 0.24 に近い
    c.append(("1章: 3階まで階段の時間の真ん中は 約 2×3.5÷0.24 ＝ 29秒（±2秒。ショートの 29.0秒）", n3["med_st_u"], 2 * 3.5 / 0.24, 2.0))
    sm = R["samples"]
    c += [("見本: 冒頭（3階・上の階で止まったかご・階段が先）・3章（4階・かごが1階）・4章（混雑の6階）の3つがそろった",
           float(all(k in sm for k in ("open3", "look4_car1", "rush6"))), 1.0, 0.0)]
    for k, v in sm.items():
        p_ = dict(v["p"]); p_["hall"] = np.array(p_["hall"]); p_["ride_mid"] = np.array(p_["ride_mid"])
        c.append((f"見本 {k}: 残した値から計算し直した エレベーターの時刻 ＝ 記録（別に計算）", elevator(p_, 1, v["dest"])["t"], v["el_t"], 1e-9))
    check_answers(c)
    print(f"  照合 {len(c)} 件 すべて OK")
    return len(c)


def write(R, n_checks):
    OUT.mkdir(parents=True, exist_ok=True)
    js = {k: ({str(d): v for d, v in R[k].items()} if isinstance(R[k], dict) else R[k]) for k in R}
    (OUT / "data.json").write_text(json.dumps(js, ensure_ascii=False, indent=1), encoding="utf-8")
    pc = lambda x: f"{x * 100:.1f}%"
    L = [f"# 階段とエレベーター（ロング）の数字（2026-10-19・照合 {n_checks} 件 OK・各階1万回）", "",
         f"- 分かれ目（階段が先が半々になる行き先）: ふだん **{R['cross_up_normal']:.2f}階**（別の乱数 {R['cross_up_normal_again']:.2f}階）／"
         f"朝の混雑 **{R['cross_up_rush']:.2f}階**／下り **{R['cross_down_normal']:.2f}階**", "",
         "| 行き先 | 階段が先（ふだん） | 差の真ん中 | 階段 真ん中 | エレベーター 真ん中 | かご1階のとき | かご1階でないとき | 表示を見て決める 平均 | いつも階段 | いつもエレベーター | 朝の混雑 | 下り |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for D in DESTS:
        x, y = R["normal"][D], R["rush"][D]
        L.append(f"| {D}階 | **{pc(x['p_up'])}** | {x['gap_up']:+.1f}秒 | {x['med_st_u']:.0f}秒 | {x['med_el_u']:.0f}秒 | {pc(x['p_up_s1'])} | {pc(x['p_up_s23'])} | "
                 f"{x['mean_look']:.1f}秒 | {x['mean_st']:.1f}秒 | {x['mean_el']:.1f}秒 | {pc(y['p_up'])} | {pc(x['p_down'])} |")
    (OUT / "numbers.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__" and "--numbers" in sys.argv:
    R = compute()
    n = run_checks(R)
    write(R, n)
    print((OUT / "numbers.md").read_text(encoding="utf-8"))
    raise SystemExit


# ####################################################################################################
# ここから下は場面（描画・音・書き出し）。2026-10-19 追加（モデル部分は変えていない）。
# 台本: publish/kaidan-long/narration_v1.md ／ 仕様: research/kaidan_long_scenes.md
# 形と部品は sims/reji-long.py の場面部分（見開き・付箋・欄・区切り・終了画面・SPOKEN の照合・時間割）。
# ビルの断面・かご・ドア・階段を上る人・ボタンと表示の絵は sims/kaidan-elevator.py（縦型ショート）の描き方をコピーして、
# 横型の左ページに合わせて直した（元のファイルは触っていない）。エスカレーターのロングとかぶらないよう、斜めのエスカレーターは出さない。
#
# 使い方
#   python -X utf8 sims/kaidan-long.py                照合 → 本番（mp4・chapters.txt・transcript.long.txt・readings.log・stills）
#   python -X utf8 sims/kaidan-long.py --scenecheck   場面の照合だけ
#   python -X utf8 sims/kaidan-long.py --stills       要所の静止画と sheet.png（out/kaidan-long/stills_v1/）。--at 12.3,40.5 なら指定した秒だけ
#   python -X utf8 sims/kaidan-long.py --readings     合成エンジンが読むカナ
#   python -X utf8 sims/kaidan-long.py --wraps        字幕の折り返しを全部表示
#   python -X utf8 sims/kaidan-long.py --preview      960×540・15fps の確認用
#   --fake-voice をつけると、AivisSpeech なしで長さを見積もる（無音。静止画の確認用。本番では使えない）
# ####################################################################################################
import re as _re
from dataclasses import dataclass

import cairo

from engine import core, note
from engine import longform as lf
from engine.core import (beat, bell, blip, chord, clamp01, ease, ease_out, fill, hexrgb, riser, rrect, shimmer, text,
                         text_width, thump, tick, whoosh)
from engine.note import INK, PENCIL, RED, STICKY, pen_circle, pen_line, sticky
from engine.voice import split_reading

VOICE_DIR = OUT / "voice"
RX = 1050                                            # 右ページの書き出しの x
RCX = 1415                                           # 右ページの中央
FAKE = "--fake-voice" in sys.argv
BLUE = "#3f78d0"                                     # エレベーターの人の印
BLUE_L = "#6a93cf"
ORANGE = "#e0892a"
GREEN = "#3f9a6a"
SUMI = "#3b4252"                                     # 階段の人（墨）
PENCIL_T = "#454d62"                                 # 補足の文字（v5: 鉛筆色 #6b7285 だと小さい字が薄いので濃くした）


def ihalf(x):
    """画面・声に出す丸め（四捨五入。Python の round の偶数丸めは使わない）"""
    return int(math.floor(float(x) + 0.5))


# ============================================================
# 台本 → 時間割（ナレーションは publish/kaidan-long/narration_v1.md の「- 」の行。文言は変えていない。数字の読みはエンジンが正しく読むので、読みの指定は使っていない）
#   間: 数字を言う文のあとは 0.5秒（_breathe）。章の境目は +0.35秒。冒頭の早回し・各章の「（無音）」は Gap
#   区切り（アイキャッチ）は 3章の終わりと 4章の章カードの間（約4秒・声なし・足音）
# ============================================================
CH_TITLES = ["何階まで、階段が早い？", "では、3階なら？", "では、何階で逆転する？", "では、表示を見てから決めたら？",
             "では、朝の混雑なら？", "では、下りなら？", "まとめ"]
SPEED_V = 1.0
EYE_GAP = 4.0                                        # 区切り（ここまで／ここから）の長さ。声なし
# 無音の早回しの長さ（台本は「約3〜4秒」。見える長さに延ばした所は報告に書く）
G_SEC = dict(g0=16.0, g1=6.0, g2=8.0, g3=9.0, g4=14.0, g5=5.0)


def _items(g_q=0.0, g_end_extra=0.0):
    """g_q・g_end_extra: 最後の問いかけ（c6_7）を終了画面の前に置くための間（準備で計算する）"""
    C, G = lf.Chapter, lf.Gap

    def L(*a, **k):
        k.setdefault("speed", SPEED_V)
        return lf.Line(*a, **k)
    return [
        C(CH_TITLES[0], id="ch0"),
        L("c0_0", "エレベーターを待つか、階段で行くか、迷ったことはありませんか？", pause=0.5),
        L("c0_1", "エレベーターのほうが速そうですが、待っている時間もありますよね。", pause=0.5),
        L("c0_2", "ふたりが同時に、1階を出発します。", pause=0.4),
        L("c0_3", "行き先は、3階です。", pause=0.5),
        L("c0_4", "ひとりは階段を上り、もうひとりはエレベーターを待ちます。", pause=0.5),
        L("c0_5", "どちらが先に着くでしょうか。", pause=0.3),
        L("c0_5b", "エレベーターのかごは、上の階にいます。", pause=0.1),
        G("g0", G_SEC["g0"]),
        L("c0_6", "階段の人のほうが、先に着きました。", pause=0.6),
        L("c0_7", "では、もっと上の階なら、どうでしょう。", pause=0.5),
        L("c0_8", "何階までなら、階段のほうが早いのでしょうか。", pause=0.5),
        L("c0_9", "あなたは、何階までなら階段派ですか？", pause=0.6),
        L("c0_10", "この動画では、ビルの階段とエレベーターを1万回ずつ競わせて、分かれ目の階を確かめます。", pause=0.5),
        L("c0_11", "ふだんのビルと、朝の混雑と、下りで、答えは変わります。", pause=1.0),
        C(CH_TITLES[1], id="ch1", gap=1.4),
        L("c1_0", "この章では、さっきの3階までの競争を、くり返し確かめます。", pause=0.4),
        L("c1_1", "建物は、エレベーターが1台の、ふつうのビルとします。", pause=0.5),
        L("c1_2", "階段を上る速さは、人によって少しずつ違います。", pause=0.5),
        L("c1_3", "エレベーターの、人が乗る箱を、「かご」と呼びます。", pause=0.5),
        L("c1_4", "エレベーターは、ボタンを押したとき、かごがどこにいるかで、来るまでの時間が変わります。", pause=0.5),
        L("c1_5", "かごが1階で止まっていることもあれば、上の階にいることもあります。", pause=0.5),
        L("c1_6", "同じように、1万回ためしてみます。", pause=0.1),
        G("g1", G_SEC["g1"]),
        L("c1_7", "階段の人が先に着いたのは、6割の回でした。", pause=0.5),
        L("c1_8", "着く時間の差は、ほんの数秒です。", pause=0.5),
        L("c1_9", "ただし、かごが1階にいた回は、ほとんどエレベーターの勝ちでした。", pause=0.5),
        L("c1_10", "エレベーターは、乗ってからは速いのですが、来るまでと、ドアの開け閉めに時間がかかるのです。", pause=0.5),
        L("c1_11", "この章で分かったことを、まとめます。", pause=0.3),
        L("c1_12", "3階までなら、階段のほうが、少しだけ先に着く回が多いです。", pause=0.8),
        C(CH_TITLES[2], id="ch2", gap=1.2),
        L("c2_0", "この章では、上る階を増やすと、どこで逆転するかを確かめます。", pause=0.4),
        L("c2_1", "あなたは、何階までなら階段派ですか？", pause=0.5),
        L("c2_2", "行き先の階を、ひとつずつ上へ変えていきます。", pause=0.5),
        L("c2_3", "階段の時間は、上る階の数に合わせて、どんどん長くなります。", pause=0.5),
        L("c2_4", "エレベーターは、上の階に行っても、時間があまり増えません。", pause=0.5),
        L("c2_4c", "待つ時間と、ドアの開け閉めの時間が、ほとんどだからです。", pause=0.5),
        L("c2_4b", "階ごとに、階段が先に着いた回の割合を、グラフにしていきます。", pause=0.4),
        L("c2_5", "階段が先に着く回のほうが多い階のうち、いちばん高い階を、「分かれ目」と呼びます。", pause=0.1),
        G("g2", G_SEC["g2"]),
        L("c2_6", "分かれ目は、3階でした。", pause=0.5),
        L("c2_7", "4階から上は、エレベーターが先に着く回のほうが多くなります。", pause=0.5),
        L("c2_8", "てっぺんの10階では、階段が先に着く回は、ほとんどありませんでした。", pause=0.5),
        L("c2_9", "この章で分かったことを、まとめます。", pause=0.3),
        L("c2_10", "ふだんのビルでは、分かれ目は、3階です。", pause=0.8),
        C(CH_TITLES[3], id="ch3", gap=1.2),
        L("c3_0", "この章では、エレベーターのかごがどこにいるかを見てから、決める場合を確かめます。", pause=0.4),
        L("c3_1", "エレベーターのボタンの上には、かごが何階にいるかの表示がありますよね。", pause=0.5),
        L("c3_2", "あなたは、表示を見てから決める派ですか？", pause=0.5),
        L("c3_3", "決めごとは、かごが1階にいればエレベーター、いなければ階段、とします。", pause=0.5),
        L("c3_3b", "いつも階段の人と、いつもエレベーターの人と、くらべます。", pause=0.1),
        G("g3", G_SEC["g3"]),
        L("c3_4", "3階と4階では、表示を見てから決めるのが、いちばん早く着きました。", pause=0.5),
        L("c3_5", "かごが1階にいれば、待つ時間がほとんどないからです。", pause=0.5),
        L("c3_6", "ところが、5階から上では、表示を見て階段にすると、かえって遅くなりました。", pause=0.5),
        L("c3_7", "5階から上は、かごがどこにいても、エレベーターのほうが先に着く回が多いのです。", pause=0.5),
        L("c3_8", "反対に、2階なら、表示を見るまでもなく、階段で行くのがいちばんでした。", pause=0.5),
        L("c3_9", "この章で分かったことを、まとめます。", pause=0.3),
        L("c3_10", "表示を見てから決めるのが得なのは、3階と4階だけです。", pause=0.8),
        G("eye", EYE_GAP),                           # 区切り（アイキャッチ。声なし・約4秒。章ではない。chapters.txt に入れない）
        C(CH_TITLES[4], id="ch4", gap=1.2),
        L("c4_0", "この章では、朝の混雑で、エレベーターが混んでいる場合を確かめます。", pause=0.4),
        L("c4_1", "朝は、エレベーターに乗る人が多く、途中の階で何度も止まりますよね。", pause=0.5),
        L("c4_2", "かごは、ほとんどの回で、ほかの人を運んでいるとします。", pause=0.5),
        L("c4_3", "途中の階で止まることも、ふだんより増えるとします。", pause=0.1),
        G("g4", G_SEC["g4"]),
        L("c4_4", "朝の混雑では、分かれ目が、7階まで上がりました。", pause=0.5),
        L("c4_5", "7階では、階段が先に着く回のほうが、わずかに多いだけです。", pause=0.5),
        L("c4_6", "混んだ朝は、思ったより上の階まで、階段のほうが早いのです。", pause=0.5),
        L("c4_7", "この章で分かったことを、まとめます。", pause=0.3),
        L("c4_8", "エレベーターが混む朝は、分かれ目が、ずっと上の階になります。", pause=0.8),
        C(CH_TITLES[5], id="ch5", gap=1.2),
        L("c5_0", "この章では、上の階から1階へ下りる場合を確かめます。", pause=0.4),
        L("c5_1", "階段は、上りより下りのほうが、速く歩けます。", pause=0.5),
        L("c5_2", "エレベーターは、上りでも下りでも、かかる時間はあまり変わりません。", pause=0.4),
        L("c5_2b", "下りでは、階段がどこまで勝つかを、1万回ためします。", pause=0.1),
        G("g5", G_SEC["g5"]),
        L("c5_3", "下りでは、分かれ目は、5階でした。", pause=0.5),
        L("c5_4", "5階から下りるなら、階段のほうが、先に着く回が多いのです。", pause=0.5),
        L("c5_5", "この章で分かったことを、まとめます。", pause=0.3),
        L("c5_6", "下りなら、分かれ目は、5階です。", pause=0.8),
        C(CH_TITLES[6], id="ch6", gap=1.2),
        L("c6_0", "最後に、この動画で分かったことを、まとめます。", pause=0.4),
        L("c6_1", "ふだんのビルを上るなら、分かれ目は、3階です。", pause=0.4),
        L("c6_2", "3階と4階なら、エレベーターの表示を見てから決めるのが、いちばん早いです。", pause=0.4),
        L("c6_3", "朝の混雑では、分かれ目が、7階まで上がります。", pause=0.4),
        L("c6_4", "下りなら、分かれ目は、5階です。", pause=0.5),
        L("c6_5", "もちろん、この動画のビルは、作り物のビルです。", pause=0.3),
        L("c6_6", "階段を何階も上ると疲れますが、この動画では、疲れて遅くなることは、ないことにしています。", pause=0.4),
    ] + ([G("g_q", g_q)] if g_q > 0 else []) + [
        L("c6_7", "次にエレベーターの前に立ったら、あなたはどうしますか？", pause=1.0),
        L("c6_8", "このチャンネルでは、身近な疑問を、シミュレーションで確かめる動画をあげています。"),
        L("c6_9", "チャンネル登録してもらえると、うれしいです。", pause=0),
        G("g_end", 2.0 + g_end_extra),   # 言い終わって約2秒で終わる（雨・合戦・エスカレーター・行列ロングと同じ）。足りない分は終了画面の後ろに足す
    ]


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


# 字幕の折り返しを指定する文（自動だと語の途中で折れるもの。--wraps で見て足す）
_SUB_BREAK = {
    "エレベーターの時間は、待つ時間とドアの時間が大きいので、あまり長くなりません。": ["エレベーターの時間は、", "待つ時間とドアの時間が大きいので、あまり長くなりません。"],
    "いちばん上の10階では、階段が先に着く回は、ほとんどありませんでした。": ["いちばん上の10階では、", "階段が先に着く回は、ほとんどありませんでした。"],
    "この章では、エレベーターのかごがどこにいるかを見てから、決める場合を確かめます。": ["この章では、エレベーターのかごがどこにいるかを", "見てから、決める場合を確かめます。"],
    "7階では、階段が先に着く回のほうが、わずかに多いだけです。": ["7階では、", "階段が先に着く回のほうが、わずかに多いだけです。"],
    "分かれ目のあたりでは、エレベーターの表示を見てから決めると、いちばん早く着きます。": ["分かれ目のあたりでは、エレベーターの", "表示を見てから決めると、いちばん早く着きます。"],
}
_wrap_auto = lf.wrap_subtitle
lf.wrap_subtitle = lambda s, limit=lf.SUB_MAX: _SUB_BREAK.get(s.replace("\n", "")) or _wrap_auto(s, limit)

# 一呼吸（雨・エスカレーター・行列・レジのロングと同じ値）
VOICE_PAUSES = (0.10, 0.22)
NUM_BREATH = 0.5                                     # 2026-10-15 ユーザー指示: 数字を言った文のあとは 0.5秒
CH_BREATH = 0.35


def _breathe(items):
    out = []
    for it in items:
        if isinstance(it, lf.Line) and any(ch.isdigit() for ch in split_reading(it.text)[0]):
            it = lf.Line(it.id, it.text, pause=it.pause + NUM_BREATH, speed=it.speed)
        elif isinstance(it, lf.Chapter) and it.id not in (None, "ch0"):
            it = lf.Chapter(it.title, id=it.id, gap=it.gap + CH_BREATH)
        out.append(it)
    return out


def _voice_synth(text_, cache_dir, **kw):
    from engine import voice
    return voice.synth(text_, cache_dir, pauses=VOICE_PAUSES, **kw)


# ============================================================
# 小さな道具（レジのロングと同じ）
# ============================================================
def lerp(a, b, u):
    return a + (b - a) * u


def fade(t, t0, d=0.3):
    return ease_out(clamp01((t - t0) / d))


def out_fade(t, t1, d=0.35):
    return 1 - clamp01((t - t1) / d)


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
    """白い下地つきの札"""
    if a <= 0.003 or progress <= 0:
        return
    w = text_width(s, size) + 26
    cx = x + w / 2 - 13 if align == "left" else x
    ctx.set_source_rgba(1, 1, 1, 0.88 * a)
    rrect(ctx, cx - w / 2, y - size * 0.72, w, size * 1.44, 10)
    ctx.fill()
    lf.write_on(ctx, s, cx, y, size, col, progress, align="center", alpha=a)


def mini_sticky(ctx, s, x, y, size, color="yellow", fg=INK, a=1.0, tilt=-0.02, align="center"):
    """余白の小さい付箋。(x, y) は中心（align='left' なら左端）"""
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


def hand_title(ctx, s, x, y, size, seed, alpha=1.0, color=INK):
    """1字ずつ少し傾けた手書きの見出し。重なりの検査には1行として記録する"""
    saved = core._LOG
    core._LOG = None
    w = note.hand_text(ctx, s, x, y, size, color, seed=seed, alpha=alpha)
    core._LOG = saved
    if saved is not None and alpha > 0.1:
        xs, ys = zip(*(ctx.user_to_device(px, py) for px, py in ((x, y - size / 2), (x + w, y + size / 2))))
        saved.append((core._CUR_T, s, min(xs), min(ys), max(xs), max(ys), abs(ctx.user_to_device_distance(0, size)[1])))
    return w


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
RES = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
SMP = RES["samples"]
_syn = _fake_synth if FAKE else _voice_synth
# v6（2026-10-19 ユーザー指摘「7:20 の数秒の無言をなくす」）: 終了画面を20秒にそろえるための無音（問いかけの前 4秒）をやめ、
# 絵が切り替わるだけの間 0.5秒にした。終了画面は c6_6 を言い終わって 0.3秒後から最後まで（約16秒・YouTube の終了画面は5秒以上でよい）
tl = lf.Timeline(_breathe(_items(0.5, 0.0)), VOICE_DIR, lead=2.0, synth=_syn)
S, E = tl.start, tl.end
DUR = tl.duration


def dur(i):
    return E(i) - S(i)


def mid(i, f=0.5):
    return S(i) + f * dur(i)


# ============================================================
# 絵: ビルの断面・階段・エレベーターのかご・ドア・ボタンと表示・人
#   sims/kaidan-elevator.py（縦型ショート）の draw_person / draw_flight / draw_building / draw_elevator / car_state / stair_state / elev_state を
#   コピーして、横型の左ページ（幅 905）に収まるよう直した。直した所: 建物の横幅を 735 に詰めた（廊下を短く）／行き先 D と建物の階数 n を引数にした／
#   かごの出入り（降りる人数 n_out・乗る時刻）は log から割り出した／ほかの人（灰色）をかごに乗せた／階の表示の矢印は図形で描いた。
#   斜めのエスカレーターは出さない。
# ============================================================
FH = 144.0                                        # 1階ぶんの高さ（場面の px）。v3: 人の高さ P_H をドアの約 3/4 にするため 135 → 144（ドア 104 → 128）
GROUND = 735.0                                    # 1階の床
BX0, BX1 = 120.0, 855.0                           # 建物の左右の壁
ST_X1 = 420.0                                     # 階段室の右の壁
FL_A, FL_B, LAND_R = 170.0, 350.0, 405.0          # 階段の下端・上端・中の踊り場の右端
SH_X0, SH_X1 = 650.0, 855.0                       # 昇降路
CAR_X0, CAR_X1 = 664.0, 806.0                     # かご
CAR_H, DOOR_H, P_H = 126.0, 128.0, 100.0          # 人はドアの約 0.78（v3。ホール拡大の絵は 0.75）
B_WAIT_X, B_RIDE_X = 560.0, 740.0                 # エレベーターを待つ位置・かごの中の位置
BTN_X = 612.0
HALL_FLAG_X = 515.0
RIDER_SLOTS = (692.0, 716.0, 740.0, 764.0, 788.0) # ほかの人（灰色）がかごの中に立つ位置
WALL, SLAB, CARC, SHAFT = "#d9d2c2", "#c9bfa9", "#fff6d8", "#e6e1d5"
GRAY_P = "#a9afbb"
AX, GS = 130.0, 905.0                             # 建物の左端と地面の、画面の位置


def floor_y(k):
    return GROUND - (k - 1) * FH


class Cam:
    """場面の座標 → 左ページの画面。n 階建てが縦に収まる倍率"""

    def __init__(self, n):
        self.SC = min(1.04, 700.0 / (n * FH + 20))

    def sx(self, x):
        return AX + (x - BX0) * self.SC

    def sy(self, y):
        return GS + (y - GROUND) * self.SC

    def apply(self, ctx):
        ctx.translate(AX, GS)
        ctx.scale(self.SC, self.SC)
        ctx.translate(-BX0, -GROUND)

    def text(self, ctx, s, x, y, size, color=INK, align="center", alpha=1.0, bold=True):
        text(ctx, s, self.sx(x), self.sy(y), max(36.0, size * self.SC), color, align=align, alpha=alpha, bold=bold)


def flight_pos(t, d, v, a):
    """動き出してから t 秒の位置（0〜d）。ショートの flight_pos をコピー"""
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


class TimeMap:
    """動画の秒 → 計算の秒 τ。早回しは区間ごとに速さを変えてよいが、順番と相対の速さは見本の記録どおり"""

    def __init__(self, knots):
        self.tv = np.array([k[0] for k in knots], float)
        self.tau = np.array([k[1] for k in knots], float)
        assert np.all(np.diff(self.tv) > 0) and np.all(np.diff(self.tau) > 0), knots

    def __call__(self, t):
        return float(np.interp(t, self.tv, self.tau))

    def t_of(self, tau):
        return float(np.interp(tau, self.tau, self.tv))


STATIC = TimeMap([(-2.0, 0.0), (-1.0, 1e-6)])         # 早回ししない（τ=0 のまま）


class Sc:
    """見本1回ぶん（data.json の samples.*）の絵の状態。かごの動きは log（wait / move / stop）どおり"""

    def __init__(self, key):
        s = SMP[key]
        self.key, self.p, self.n, self.D = key, s["p"], s["p"]["n"], s["dest"]
        self.log = [tuple(e) for e in s["log"]]
        self.T_st, self.T_el = float(s["stairs"]), float(s["el_t"])
        stops = [e for e in self.log if e[0] == "stop"]
        self.final = stops[-1]                         # 自分が降りる止まり
        self.board = [e for e in stops if e[3] == 1][-1]   # 自分が乗る止まり（1階）
        b = self.board
        self.n_out = max(0, ihalf((b[5] - b[4] - self.p["dwell"] - T_IN) / T_OUT))   # 乗る前に降りる人数（log から逆算）
        self.pre = [e for e in stops if e[1] < b[1] - 1e-9]                          # 乗る前のほかの止まり
        self.cam = Cam(self.n)
        ex = [(e[4], e[3]) for e in self.pre] + [(b[4] + i * T_OUT, 1) for i in range(self.n_out)]
        self.exits = ex[:len(RIDER_SLOTS)]             # ほかの人（灰色）が降りる時刻と階
        self.t_board = b[4] + self.n_out * T_OUT       # 自分が乗り始める
        self.stair_flights = 2 * (self.D - 1)

    # ---- かご ----
    def car_state(self, tau):
        """かごの位置（階。小数）・動いている向き・各階のドアの開き具合 {階: 0〜1}"""
        p = self.p
        pos, mv, doors = float(p["f0"]), 0, {}
        for ev in self.log:
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
                mv = (1 if b > a else -1) if x > 0 else 0
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

    # ---- 階段の人 ----
    def stair_state(self, tau):
        """階段の人: 場面の足元 (x, y)・向き（1 右 / −1 左）・歩いているか・上った高さ（階ぶん）"""
        nf, T, D = self.stair_flights, self.T_st, self.D
        unit = T / (nf * 0.8 + (nf - 1) * 0.2)
        half = FH / 2
        if tau >= T:
            dt = tau - T
            return dict(x=FL_A - 34 * clamp01(dt / 1.0), y=floor_y(D), face=-1, walk=dt < 1.0, h=D - 1.0, done=True)
        if tau <= 1e-3:
            return dict(x=FL_A, y=GROUND, face=1, walk=False, h=0.0, done=False)
        u = tau / unit
        for j in range(nf):
            y0 = GROUND - j * half
            right = j % 2 == 0
            if u < 0.8:
                k = u / 0.8
                x = FL_A + (FL_B - FL_A) * k if right else FL_B - (FL_B - FL_A) * k
                return dict(x=x, y=y0 - half * k, face=1 if right else -1, walk=True, h=(j + k) / 2, done=False)
            u -= 0.8
            if j < nf - 1:
                if u < 0.2:
                    k = u / 0.2
                    x = FL_B + 30 * math.sin(math.pi * k) if right else FL_A - 30 * math.sin(math.pi * k)
                    face = (1 if k < 0.5 else -1) if right else (-1 if k < 0.5 else 1)
                    return dict(x=x, y=y0 - half, face=face, walk=True, h=(j + 1) / 2, done=False)
                u -= 0.2
        return dict(x=FL_A, y=floor_y(D), face=-1, walk=False, h=D - 1.0, done=True)

    # ---- エレベーターの人 ----
    def elev_state(self, tau):
        pos, mv, doors = self.car_state(tau)
        cy = GROUND - (pos - 1) * FH
        b, f = self.board, self.final
        out0 = f[4]                                    # 降りる階のドアが開き終わる
        if tau < 0.9:                                  # ボタンを押す
            return dict(x=B_WAIT_X, y=GROUND, face=1, walk=False, reach=math.sin(math.pi * clamp01(tau / 0.9)) if tau > 0 else 0.0,
                        status="wait", done=False, ride=False)
        if tau < self.t_board:
            return dict(x=B_WAIT_X, y=GROUND, face=1, walk=False, reach=0.0, status="wait", done=False, ride=False)
        if tau < self.t_board + T_IN:                  # 乗りこむ
            k = (tau - self.t_board) / T_IN
            return dict(x=B_WAIT_X + (B_RIDE_X - B_WAIT_X) * ease(k), y=GROUND, face=1, walk=True, reach=0.0,
                        status="board", done=False, ride=False)
        if tau < out0:
            return dict(x=B_RIDE_X, y=cy, face=-1, walk=False, reach=0.0, status="ride" if mv != 0 else "door", done=False, ride=True)
        if tau < out0 + T_OUT:                         # 降りる
            k = (tau - out0) / T_OUT
            return dict(x=B_RIDE_X + (HALL_FLAG_X + 40 - B_RIDE_X) * k, y=floor_y(self.D), face=-1, walk=True, reach=0.0,
                        status="out", done=False, ride=False)
        dt = tau - out0 - T_OUT
        return dict(x=HALL_FLAG_X + 40 - 50 * clamp01(dt / 0.8), y=floor_y(self.D), face=-1, walk=dt < 0.8, reach=0.0,
                    status="done", done=True, ride=False)

    def riders(self, tau):
        """ほかの人（灰色）: [(x, y, 濃さ)]。かごの中に立ち、止まりでドアが開くと降りて、廊下で薄くなる"""
        pos, mv, doors = self.car_state(tau)
        cy = GROUND - (pos - 1) * FH
        out = []
        for r, (t_ex, fl) in enumerate(self.exits):
            x_in = RIDER_SLOTS[r]
            if tau < t_ex:
                out.append((x_in, cy, 1.0))
            elif tau < t_ex + 1.0:
                k = (tau - t_ex) / 1.0
                out.append((x_in + (SH_X0 - 60 - x_in) * ease(k), floor_y(fl), 1.0 - 0.5 * k))
            elif tau < t_ex + 2.4:
                k = (tau - t_ex - 1.0) / 1.4
                out.append((SH_X0 - 60 - 30 * k, floor_y(fl), 0.5 * (1 - k)))
        return out


# ---------- 人（ペン描きの線）: ショートの draw_person をコピー ----------
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


DRAWN = [0]                                          # 描いた人の数（検査用）


def draw_person(ctx, x, gy, h, col, phase, amp=1.0, face=1, reach=0.0, climb=0.0, a=1.0):
    """横から見た歩く人。足元が (x, gy)。face=1 で右向き。reach で前の手を上げる（ボタン）。climb で膝を高く上げる（階段）"""
    if a <= 0.003:
        return
    DRAWN[0] += 1
    s = h / 150.0
    ctx.save()
    ctx.translate(x, gy)
    ctx.scale(s * face, s)
    if a < 0.997:
        ctx.push_group()
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
    if a < 0.997:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)
    ctx.restore()


# ---------- 建物の断面 ----------
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


def draw_flag(ctx, fx, y, a=1.0):
    _line(ctx, fx, y, fx, y - 70, 2.5, a=0.9 * a)
    ctx.move_to(fx, y - 70)
    ctx.line_to(fx + 30, y - 61)
    ctx.line_to(fx, y - 52)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))
    ctx.fill()


def draw_building(ctx, sc, flags=1.0, flag_floor=None):
    """ビルの断面（床・階段・昇降路・屋上・行き先の旗）。ctx は cam.apply 済み"""
    n = sc.n
    top = floor_y(n + 1)
    fill(ctx, hexrgb("#a8d68f", 0.35))                 # 地面
    ctx.rectangle(BX0 - 90, GROUND, BX1 - BX0 + 180, 60)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb("#8a6b4a", 0.45))
    ctx.set_line_width(2)
    for i in range(20):
        x = BX0 - 80 + i * 48 + 10
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
        _line(ctx, ST_X1, y - FH + 14, ST_X1, y - 120, 3.0)
        _line(ctx, SH_X0, y - FH + 14, SH_X0, y - DOOR_H - 4, 3.0)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.45))     # 部屋のドア（廊下の奥）
        ctx.set_line_width(2)
        core.rrect(ctx, 458, y - 126, 54, 126, 3)
        ctx.stroke()
    _line(ctx, BX0, top, BX0, GROUND, 4.0)
    _line(ctx, BX1, top, BX1, GROUND, 4.0)
    _line(ctx, BX0 - 12, top, BX1 + 12, top, 5.0)     # 屋上
    if flags > 0.003:                                  # 行き先の階の旗（階段の踊り場と、エレベーターの前）
        yd = floor_y(flag_floor or sc.D)
        for fx in (BX0 + 18, HALL_FLAG_X):
            draw_flag(ctx, fx, yd, flags)


def arrow_tri(ctx, cx, cy, up, size, col, a=1.0):
    """階の表示の ▲▼（図形）"""
    s = size
    d = -1 if up else 1
    ctx.move_to(cx, cy + d * s)
    ctx.line_to(cx - s * 0.9, cy - d * s * 0.7)
    ctx.line_to(cx + s * 0.9, cy - d * s * 0.7)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.fill()


def draw_elevator(ctx, sc, tau, lamp=True, car=None):
    """昇降路のロープ・おもり・かご・各階の乗り場のドア・階の表示窓・ボタン。ctx は cam.apply 済み。
    car=(階, 向き) を渡すと、記録とは別に かごをその位置で描く（冒頭の、人が出てくる前の動きのイメージ用）"""
    n = sc.n
    pos, mv, doors = sc.car_state(tau) if car is None else (car[0], car[1], {})
    cy = GROUND - (pos - 1) * FH                       # かごの床
    top = floor_y(n + 1)
    mx = (CAR_X0 + CAR_X1) / 2
    cwx = SH_X1 - 24
    cw_y = GROUND - 80 - (n - pos) / max(1, n - 1) * (GROUND - 80 - top - 40)   # おもり（かごと逆に動く）
    ctx.set_source_rgba(*hexrgb(INK, 0.6))
    ctx.set_line_width(2)
    ctx.move_to(mx, top + 14)
    ctx.line_to(mx, cy - CAR_H)
    ctx.move_to(cwx, top + 22)
    ctx.line_to(cwx, cw_y)
    ctx.stroke()
    ctx.arc((mx + cwx) / 2, top + 24, 12, 0, 2 * math.pi)
    ctx.stroke()
    fill(ctx, hexrgb("#9aa3b5", 0.9))
    ctx.rectangle(cwx - 10, cw_y, 20, 70)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.stroke()
    fill(ctx, hexrgb(CARC))                            # かご
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
    for k in range(1, n + 1):                          # 各階の乗り場のドア（開くと上へ引っこむ）・階の表示窓・ボタン
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
        fill(ctx, (1, 1, 1, 0.95))                     # 階の表示窓（ボタンの上）
        core.rrect(ctx, BTN_X - 44, y - FH + 16, 76, 46, 6)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(2)
        ctx.stroke()
        fill(ctx, (1, 1, 1, 0.95))                     # ボタン
        core.rrect(ctx, BTN_X - 8, y - 72, 16, 24, 4)
        ctx.fill_preserve()
        ctx.stroke()
        if mv != 0:
            arrow_tri(ctx, BTN_X + 19, y - FH + 39, mv > 0, 7, RED)
    b = sc.board                                       # 1階のボタンのランプ（押してから、ドアが開くまで）
    if lamp and 0.6 <= tau < b[1]:
        fill(ctx, hexrgb("#ff9f2e"))
        ctx.arc(BTN_X, floor_y(1) - 60, 5.5, 0, 2 * math.pi)
        ctx.fill()


def draw_scene_labels(ctx, sc, tau, a=1.0, hi_floor=None, car=None, red=True):
    """階の名前（左）と、各階の表示窓の数字。画面の字として描く（大きさは 36px 以上。v5）"""
    cam, n = sc.cam, sc.n
    pos, mv, _ = sc.car_state(tau) if car is None else (car[0], car[1], {})
    cf = int(round(pos))
    for k in range(1, n + 1):
        y = floor_y(k)
        cam.text(ctx, f"{k}階", BX0 - 44, y - FH / 2, 40, RED if (red and k == sc.D) else INK, alpha=a)
        cam.text(ctx, f"{cf}", BTN_X - 10, y - FH + 41, 40, INK, alpha=a)


def draw_people(ctx, sc, t, tau, a=1.0, st_alpha=1.0):
    """階段の人（墨）・エレベーターの人（青）・ほかの人（灰色）"""
    sa, sb = sc.stair_state(tau), sc.elev_state(tau)
    for (x, y, al) in sc.riders(tau):
        draw_person(ctx, x, y, P_H * 0.8, GRAY_P, 0.0, amp=0.0, face=-1, a=a * al)
    draw_person(ctx, sa["x"], sa["y"], P_H, SUMI, 2 * math.pi * 1.3 * t if sa["walk"] else 0.0,
                amp=1.0 if sa["walk"] else 0.0, face=sa["face"], climb=1.0 if (sa["walk"] and not sa["done"]) else 0.0, a=a * st_alpha)
    sway = 0.0 if sb["walk"] else 0.3 * math.sin(2 * math.pi * 0.5 * t)
    draw_person(ctx, sb["x"], sb["y"], P_H, BLUE, 2 * math.pi * 1.3 * t if sb["walk"] else sway,
                amp=1.0 if sb["walk"] else 0.2, face=sb["face"], reach=sb["reach"], a=a)


def draw_scene(ctx, sc, t, tm, a=1.0, people=1.0, flags=1.0, labels=True, show_people=True, st_alpha=1.0, car=None):
    """見本の断面1つ。tm は動画の秒→τ。a は全体の濃さ"""
    if a <= 0.003:
        return
    tau = tm(t)
    cam = sc.cam
    if a < 0.997:
        ctx.push_group()
    ctx.save()
    cam.apply(ctx)
    draw_building(ctx, sc, flags=flags)
    draw_elevator(ctx, sc, tau, lamp=car is None, car=car)
    if show_people and people > 0.003:
        draw_people(ctx, sc, t, tau, people, st_alpha)
    ctx.restore()
    if labels:
        draw_scene_labels(ctx, sc, tau, car=car, red=flags > 0.4)
    if a < 0.997:
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(a)


def arrival_times(sc, tm):
    """絵のほうで2人が着く動画の秒（階段・エレベーター）"""
    return tm.t_of(sc.T_st), tm.t_of(sc.T_el)


def draw_arrival_tags(ctx, sc, t, tm, a=1.0, secs=True):
    """着いた順の札（先に着いた／あとで着いた）。着いた人の頭の上あたり（白い下地つき）。v5: 36px。2枚が重ならないよう、右の札は左の札のあとに置く"""
    cam = sc.cam
    t_s, t_e = arrival_times(sc, tm)
    first = "st" if t_s < t_e else "el"
    items = (("st", t_s, "階段", SUMI, ihalf(sc.T_st)), ("el", t_e, "エレベーター", BLUE, ihalf(sc.T_el)))
    labs = {}
    for who, ta, nm, col, secs_ in items:
        labs[who] = ("先に着いた" if who == first else "あとで着いた") + (f" {secs_}秒" if secs else "")
    w_st = text_width(labs["st"], 36) + 26
    for who, ta, nm, col, secs_ in items:
        if t < ta:
            continue
        yd = floor_y(sc.D)
        if who == "st":
            x0 = cam.sx(BX0 + 6) - 80
        else:
            x0 = max(cam.sx(HALL_FLAG_X - 10), cam.sx(BX0 + 6) - 80 + w_st + 28)
            x0 = min(x0, 940 - (text_width(labs["el"], 36) + 26))
        y0 = cam.sy(yd - 148)
        tag(ctx, labs[who], x0, y0, 36, RED if who == first else PENCIL_T, a * fade(t, ta, 0.3), align="left")


# ============================================================
# 見本の断面・早回しの時間の進み・1万回（3階）の結果
# ============================================================
SC0, SC3, SC4 = Sc("open3"), Sc("look4_car1"), Sc("rush6")
TM0 = TimeMap([(S("g0") + 0.2, 0.0), (E("g0") - 0.5, max(SC0.T_st, SC0.T_el) + 3.0)])
TM3 = TimeMap([(S("g3") + 0.2, 0.0), (E("g3") - 0.5, max(SC3.T_st, SC3.T_el) + 3.0)])
TM4 = TimeMap([(S("g4") + 0.2, 0.0), (E("g4") - 0.4, max(SC4.T_st, SC4.T_el) + 3.0)])


def _run3():
    """3階の1万回（data.json と同じ乱数の種）。階段が先か・かごがどこにいたか。時間がかかるので out/kaidan-long/run3_cache.npz に残す"""
    f = OUT / "run3_cache.npz"
    if f.exists():
        z = np.load(f)
        return z["st_u"], z["el_u"], z["scen"]
    r = run(SEED_MAIN, 3)
    np.savez(f, st_u=r["st_u"], el_u=r["el_u"], scen=r["scen"])
    return r["st_u"], r["el_u"], r["scen"]


RUN3_ST, RUN3_EL, RUN3_SCEN = _run3()
RUN3_FIRST_ST = RUN3_ST < RUN3_EL                           # 階段が先に着いた回

# ---------- 画面と声に出す数字（すべて data.json から。四捨五入。細かい数字は付箋と欄だけ） ----------
NORM, RUSH_, AGAIN = RES["normal"], RES["rush"], RES["normal_again"]
DEST_LIST = list(range(2, 11))
PU = [NORM[str(D)]["p_up"] for D in DEST_LIST]              # ふだんの上り
PR = [RUSH_[str(D)]["p_up"] for D in DEST_LIST]             # 朝の混雑
PD = [NORM[str(D)]["p_down"] for D in DEST_LIST]            # 下り
TOP_UP, TOP_RUSH, TOP_DOWN = RES["top_up_normal"], RES["top_up_rush"], RES["top_down_normal"]
_pc = lambda v: ihalf(v * 100)
N3 = NORM["3"]
SH = dict(
    P3=_pc(N3["p_up"]), P3W=ihalf(N3["p_up"] * 10),                 # 3階 階段が先 60%・「6割」
    GAP5=ihalf(N3["gap_up"]), S1_9=_pc(N3["p_up_s1"]),               # 差の真ん中 5秒・かごが1階 9%
    P4=_pc(NORM["4"]["p_up"]), P10=_pc(NORM["10"]["p_up"]),
    R7=_pc(RUSH_["7"]["p_up"]), D5=_pc(NORM["5"]["p_down"]),
    SCEN=tuple(ihalf(x * 10) for x in NORMAL["scen"]),               # かごの場所 3割・3割・4割
    RUSH_BUSY=ihalf(RUSH["scen"][2] * 10), RUSH_STOP=ihalf(RUSH["hall"] * 10),   # 朝: ほかの人を運んでいる 8割・途中の階で止まる 3割
    DOWN_X=round(sum(DOWN_RATIO) / 2, 1),                            # 下りは上りの約1.3倍の速さ
    CM24=ihalf(STAIR_MED * 100),                                     # 階段 1秒に高さ約24cm
    FL_LO=max(5, 3), FL_HI=max(8, 3 + 3),                            # 5〜8階建て（D=3）
)
LOOK_ROWS = [3, 4, 5, 2]                                            # 表の行（台本の順）


def look_row(D):
    x = NORM[str(D)]
    return ihalf(x["mean_look"]), ihalf(x["mean_st"]), ihalf(x["mean_el"])


# 声に出す数字（文ごと）。scene_checks で、台本の文の数字がこれと1つ残らず一致するかを見る。「N回にM回」は1つの数字として数える。
SPOKEN = {
    "c0_2": ["1階"], "c0_3": [f"{SMP['open3']['dest']}階"], "c0_10": ["1万回"], "c5_2b": ["1万回"],
    "c1_0": [f"{SMP['open3']['dest']}階"], "c1_1": ["1台"], "c1_5": ["1階"], "c1_6": ["1万回"], "c1_7": [f"{SH['P3W']}割"],
    "c1_9": ["1階"], "c1_12": [f"{SMP['open3']['dest']}階"],
    "c2_6": [f"{TOP_UP}階"], "c2_7": [f"{TOP_UP + 1}階"], "c2_8": [f"{DEST_LIST[-1]}階"], "c2_10": [f"{TOP_UP}階"],
    "c3_3": ["1階"], "c3_4": [f"{TOP_UP}階", f"{TOP_UP + 1}階"], "c3_5": ["1階"],
    "c3_6": [f"{TOP_UP + 2}階"], "c3_7": [f"{TOP_UP + 2}階"], "c3_8": [f"{DEST_LIST[0]}階"], "c3_10": [f"{TOP_UP}階", f"{TOP_UP + 1}階"], "c6_2": [f"{TOP_UP}階", f"{TOP_UP + 1}階"],
    "c4_4": [f"{TOP_RUSH}階"], "c4_5": [f"{TOP_RUSH}階"],
    "c5_0": ["1階"], "c5_3": [f"{TOP_DOWN}階"], "c5_4": [f"{TOP_DOWN}階"], "c5_6": [f"{TOP_DOWN}階"],
    "c6_1": [f"{TOP_UP}階"], "c6_3": [f"{TOP_RUSH}階"], "c6_4": [f"{TOP_DOWN}階"],
}
PCT_OK = {SH[k] for k in ("P3", "P4", "P10", "R7", "D5", "S1_9")} | {0, 50, 100}


# ============================================================
# 左ページ
# ============================================================
def clip_left(ctx):
    ctx.rectangle(40, 30, 905, 905)
    ctx.clip()


def title_mark(ctx, t, t0, a=1.0):
    """題字「階段とエレベーター」＋赤い下線（0秒目から。下線は書くように引く）"""
    w = hand_title(ctx, "階段とエレベーター", 112, 84, 76, seed=77, alpha=a)
    pen_line(ctx, 106, 130, 106 + w + 14, 126, RED, seed=5, width=8, progress=clamp01((t - t0) / 0.3), alpha=a)


def legend_people(ctx, a=1.0, y=178, items=None):
    """階段の人（墨）・エレベーターを待つ人（青）の色の見本"""
    items = items or ((SUMI, "階段の人"), (BLUE, "エレベーターを待つ人"))
    tot = sum(36 + text_width(lab, 36) for _, lab in items) + 30 * (len(items) - 1)
    x = min(112, 945 - tot - 8)                     # v5: 36px。3つ並べても左ページに収める
    for col, lab in items:
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.arc(x + 12, y, 12, 0, 2 * math.pi)
        ctx.fill()
        text(ctx, lab, x + 36, y, 36, INK, align="left", alpha=a)
        x += 36 + text_width(lab, 36) + 30


def ring_floor_label(ctx, sc, a, progress=1.0, seed=9):
    cam = sc.cam
    pen_circle(ctx, cam.sx(BX0 - 44), cam.sy(floor_y(sc.D) - FH / 2), 52, 38, RED, seed=seed, width=4.5, progress=progress, alpha=a)


OPEN_CAR_SEC = 8.0                                   # 冒頭、ふたりが出てくる前に、かごが5階→1階→5階と動く長さ（イメージ。見本の記録とは別）


def open_car(t):
    """冒頭（0〜8秒）のかごの動き: 5階で待つ 0.6秒 → 1階へ 3.2秒 → 1階で 1.0秒 → 5階へ 3.2秒。返り値 (階, 向き)。8秒以降は None（見本の記録どおり）"""
    if t >= OPEN_CAR_SEC:
        return None
    if t < 0.6:
        return 5.0, 0
    if t < 3.8:
        return 5.0 - 4.0 * ease((t - 0.6) / 3.2), -1
    if t < 4.8:
        return 1.0, 0
    return 1.0 + 4.0 * ease((t - 4.8) / 3.2), 1


def L_open(ctx, t):
    title_mark(ctx, t, 0.0)
    pa = fade(t, S("c0_2") + 0.2, 0.5)
    fa = fade(t, S("c0_3") + 0.2, 0.4)
    draw_scene(ctx, SC0, t, TM0, 1.0, people=pa, flags=fa, car=open_car(t))
    if t >= S("c0_3") + 0.3:
        ring_floor_label(ctx, SC0, 1.0, clamp01((t - S("c0_3") - 0.3) / 0.5))
    if t >= S("c0_4") + 0.3:
        legend_people(ctx, fade(t, S("c0_4") + 0.3, 0.4))
    draw_arrival_tags(ctx, SC0, t, TM0, secs=t >= S("c0_6"))            # 秒数は「階段の人のほうが先に着きました」から（冒頭40秒の数字を3つまでにするため）


def L_places(ctx, t, a):
    """1章: ボタンを押したときのかごの場所3つ（1階で止まっている・ほかの階で止まっている・ほかの人を運んでいる）"""
    names = ("1階で止まる", "ほかの階で止まる", "人を運んでいる")
    reveal = (S("c1_5") + 0.4, mid("c1_5", 0.6), mid("c1_5", 0.97))
    fl = lambda j: 765.0 - j * 110.0
    for i in range(3):
        u = fade(t, reveal[i], 0.4) * a
        if u <= 0.003:
            continue
        x0 = 70 + i * 290
        ctx.push_group()
        fill(ctx, (1, 1, 1, 0.75))
        rrect(ctx, x0, 215, 270, 550, 14)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.8))
        ctx.set_line_width(3)
        rrect(ctx, x0, 215, 270, 550, 14)
        ctx.stroke()
        fill(ctx, hexrgb(SHAFT, 0.95))                    # 昇降路
        ctx.rectangle(x0 + 150, 225, 100, 540)
        ctx.fill()
        for j in range(6):                                # 床の線
            ctx.set_source_rgba(*hexrgb(INK, 0.55))
            ctx.set_line_width(2.4)
            ctx.move_to(x0 + 14, fl(j))
            ctx.line_to(x0 + 150, fl(j))
            ctx.stroke()
        f_car = (1.0, 4.0, 2.55)[i]                       # かごの高さ（階。小数）
        cy = fl(f_car - 1)
        fill(ctx, hexrgb(CARC))
        ctx.rectangle(x0 + 160, cy - 100, 80, 100)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.set_line_width(3)
        ctx.stroke()
        if i == 2:                                        # 人を運んでいる: 灰色の人が乗り、途中の階でドアが開く印
            for k, xx in enumerate((184, 216)):
                draw_person(ctx, x0 + xx, cy, 64, GRAY_P, 0.0, amp=0.0, face=-1)
            for j in (2, 4):
                ctx.set_source_rgba(*hexrgb(RED, 0.8))
                ctx.set_line_width(3)
                ctx.move_to(x0 + 150, fl(j) - 20)
                ctx.line_to(x0 + 150, fl(j) - 64)
                ctx.stroke()
            arrow_tri(ctx, x0 + 200, cy - 116, True, 12, RED)
            arrow_tri(ctx, x0 + 200, cy + 14, False, 12, RED)
        else:                                             # 止まっているかご: かごの下にドアの印
            ctx.set_source_rgba(*hexrgb(INK, 0.5))
            ctx.set_line_width(2.2)
            ctx.move_to(x0 + 150, cy - 70)
            ctx.line_to(x0 + 150, cy)
            ctx.stroke()
        draw_person(ctx, x0 + 60, fl(0), 78, BLUE, 0.0, amp=0.0, face=1, reach=1.0 if i == 0 else 0.0)
        ctx.set_source_rgba(*hexrgb(INK, 0.5))            # 呼ぶボタン
        core.rrect(ctx, x0 + 108, fl(0) - 66, 14, 22, 4)
        ctx.fill()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(u)
        text(ctx, names[i], x0 + 135, 806, 36, INK, alpha=u)
        text(ctx, f"{SH['SCEN'][i]}割", x0 + 135, 868, 56, RED, alpha=u)


GW, CELL, BGAP = 618, 6, 2                              # 1万回のマス目（100×100。10×10ごとにすきま）
GX0, GY0 = 183, 222
_ix = np.arange(N)
_gcx = (_ix % 100) * CELL + (_ix % 100) // 10 * BGAP
_gcy = (_ix // 100) * CELL + (_ix // 100) // 10 * BGAP
_gperm = np.random.default_rng(SEED_MAIN + 4).permutation(N)
POS_X, POS_Y = _gcx[_gperm], _gcy[_gperm]
ORDER = np.random.default_rng(SEED_MAIN + 3).permutation(N)           # マスが現れる順
from engine.parts import bgra                                          # noqa: E402
ST_C, EL_C, EMPTY_C = (np.array(bgra(c), np.uint8) for c in (SUMI, BLUE_L, "#e6dfcf"))
DIM_ST, DIM_EL = (np.array(bgra(c), np.uint8) for c in ("#b5b7bd", "#c9d6ea"))


def _grid_surface(shown, focus=None):
    """focus（True の回だけ濃く）を渡すと、それ以外の回は薄い色にする"""
    img = np.zeros((GW, GW, 4), np.uint8)
    base = np.where(RUN3_FIRST_ST[:, None], ST_C, EL_C)
    if focus is not None:
        dim = np.where(RUN3_FIRST_ST[:, None], DIM_ST, DIM_EL)
        base = np.where(focus[:, None], base, dim)
    cols = np.where(shown[:, None], base, EMPTY_C)
    for k in range(CELL - 1):
        for j in range(CELL - 1):
            img[POS_Y + k, POS_X + j] = cols
    return cairo.ImageSurface.create_for_data(memoryview(img), cairo.FORMAT_ARGB32, GW, GW, GW * 4), img


_GCACHE = {}


def draw_grid(ctx, a, n, focus_key=None):
    if a <= 0.003:
        return
    if n < N:
        shown = np.zeros(N, bool)
        shown[ORDER[:n]] = True
        surf, _img = _grid_surface(shown)
    else:
        if focus_key not in _GCACHE:
            focus = (RUN3_SCEN == 0) if focus_key == "s0" else None
            _GCACHE[focus_key] = _grid_surface(np.ones(N, bool), focus)
        surf, _img = _GCACHE[focus_key]
    ctx.set_source_surface(surf, GX0, GY0)
    ctx.paint_with_alpha(a)


def legend_sq(ctx, items, cx, y, size=36, gap=40, a=1.0):
    ws = [46 + text_width(lab, size, bold=False) for _, lab in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (col, lab), w in zip(items, ws):
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.rectangle(x, y - 15, 30, 30)
        ctx.fill()
        text(ctx, lab, x + 42, y, size, INK, align="left", bold=False, alpha=a)
        x += w + gap


# 3階の時間の内わけ（見本 open3。log から: 待つ → ドアと乗る → 動く → 降りる）
def time_parts(sc):
    b, f = sc.board, sc.final
    mv = [e for e in sc.log if e[0] == "move" and e[1] >= b[2] - 1e-9][-1]    # 乗ったあとの動き
    return [("待つ", b[1]), ("ドアと乗る", mv[1] - b[1]), ("動く", f[1] - mv[1]), ("降りる", sc.T_el - f[1])]


def draw_time_bars(ctx, sc, a, t0, t):
    """c1_10: 見本の1回で、階段とエレベーターが着くまでの時間の内わけ（横の棒）"""
    px = 20.0                                          # v5: 24 → 20（「31秒」を36px以上にしても のどにかからない）
    x0 = 100
    text(ctx, "見本の1回（3階まで）", 112, 150, 44, INK, align="left", alpha=a)
    u = ease(clamp01((t - t0) / 0.8))
    y1, y2 = 380, 540
    text(ctx, "階段", x0, y1 - 58, 40, SUMI, align="left", alpha=a)
    ctx.set_source_rgba(*hexrgb(SUMI, 0.9 * a))
    rrect(ctx, x0, y1 - 24, sc.T_st * px * u, 48, 6)
    ctx.fill()
    text(ctx, f"{ihalf(sc.T_st)}秒", x0 + sc.T_st * px * u + 18, y1, 44, SUMI, align="left", alpha=a * clamp01(u * 3 - 2))
    text(ctx, "エレベーター", x0, y2 - 58, 40, BLUE, align="left", alpha=a)
    cols = (BLUE_L, ORANGE, BLUE, "#eebb77")
    xx = x0
    for (nm, sec), col in zip(time_parts(sc), cols):
        w = sec * px * u
        ctx.set_source_rgba(*hexrgb(col, 0.92 * a))
        rrect(ctx, xx, y2 - 24, max(w - 3, 1), 48, 6)
        ctx.fill()
        if u > 0.99:
            text(ctx, nm, xx + sec * px / 2 - 1, y2 + 54, 36, INK, alpha=a)
        xx += w
    text(ctx, f"{ihalf(sc.T_el)}秒", xx + 18, y2, 44, BLUE, align="left", alpha=a * clamp01(u * 3 - 2))


def L_ch1(ctx, t):
    a_in = fade(t, S("ch1") + 0.2, 0.4)
    t_pl, t_gr, t_bar = S("c1_5") + 0.3, S("g1") - 0.05, S("c1_10") - 0.15
    a_bld = a_in * out_fade(t, t_pl, 0.4)
    a_pl = fade(t, t_pl, 0.4) * out_fade(t, t_gr, 0.4)
    a_gr = fade(t, t_gr, 0.4) * out_fade(t, t_bar, 0.4)
    a_bar = fade(t, t_bar, 0.4)
    if a_bld > 0.003:
        draw_scene(ctx, SC0, t, STATIC, a_bld, people=1.0, flags=1.0)
        if t >= S("c1_3") + 0.3:                              # 札「かご」
            cam = SC0.cam
            ta = a_bld * fade(t, S("c1_3") + 0.3, 0.3)
            xc, yc = cam.sx((CAR_X0 + CAR_X1) / 2), cam.sy(floor_y(SC0.p["f0"]) - CAR_H - 6)
            tag(ctx, "かご", xc, yc - 36, 40, RED, ta)
            pen_line(ctx, xc, yc - 12, xc, yc + 16, RED, seed=8, width=5, progress=clamp01((t - S("c1_3") - 0.5) / 0.3), alpha=ta)
            arrow_tri(ctx, xc, yc + 22, False, 11, RED, ta)
        if t >= S("c1_4") + 0.3:                              # ボタンを押す: 光る
            cam = SC0.cam
            pulse = 0.5 + 0.5 * math.sin((t - S("c1_4")) * 6.0)
            ctx.set_source_rgba(*hexrgb("#ff9f2e", 0.8 * pulse * a_bld))
            ctx.arc(cam.sx(BTN_X), cam.sy(floor_y(1) - 60), 12 * cam.SC, 0, 2 * math.pi)
            ctx.fill()
    L_places(ctx, t, a_pl)
    if a_gr > 0.003:
        text(ctx, "階段とエレベーターを、3階まで1万回ずつ", 100, 66, 40, INK, align="left", alpha=a_gr)
        text(ctx, "（1つのマス ＝ 1回）", 100, 118, 36, PENCIL_T, align="left", bold=False, alpha=a_gr)
        n = int(N * clamp01((t - S("g1") - 0.2) / (dur("g1") - 0.6)) ** 1.3)
        legend_sq(ctx, [(SUMI, "階段が先"), (BLUE_L, "エレベーターが先")], 490, 172, a=a_gr)
        focus = "s0" if t >= S("c1_9") + 0.2 else None
        if focus:
            draw_grid(ctx, a_gr, N, "s0")
            tag(ctx, "うすい色 ＝ かごが1階にいなかった回", 490, 880, 36, PENCIL_T, a_gr * fade(t, S("c1_9") + 0.3, 0.3))
        else:
            draw_grid(ctx, a_gr, n, None)
    if a_bar > 0.003:
        draw_time_bars(ctx, SC0, a_bar, t_bar + 0.2, t)


# ---------- 2章: 行き先の階を上へ。階段とエレベーターの時間（真ん中の値）の棒 ----------
TFH = 69.0                                            # 縦長の建物の1階ぶん
TY0 = 880.0
TDX = 100.0                                           # v5: 階の名前を36pxにするため、建物を右へ100px
TX0, TX1 = 60.0 + TDX, 292.0 + TDX
BAR_X0 = 330.0 + TDX
BAR_PX = 3.5                                          # 1秒 ＝ 3.5px（v5: 4px → 3.5px。棒の右端を左ページに収める）


def ty(k):
    return TY0 - (k - 1) * TFH


def draw_tall(ctx, a, flag_f, rows_u, hi, t_sel=None, label_sel=None):
    """縦長の建物（10階）と、行き先ごとの 階段・エレベーターの時間（真ん中の値）の棒。flag_f は旗の高さ（階。小数）。
    rows_u[k] は行の現れ具合。hi は 'st' / 'el' / None（強調する棒）"""
    if a <= 0.003:
        return
    ctx.push_group()
    top = ty(11)
    fill(ctx, hexrgb("#fbf7ee", 0.92))
    ctx.rectangle(TX0, top, TX1 - TX0, TY0 - top)
    ctx.fill()
    fill(ctx, hexrgb(SHAFT, 0.95))
    ctx.rectangle(TX1 - 62, top, 62, TY0 - top)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(2.4)
    for k in range(1, 12):
        ctx.move_to(TX0 - (10 if k == 11 else 0), ty(k))
        ctx.line_to(TX1 + (10 if k == 11 else 0), ty(k))
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.4))                # 階段のしるし（折り返し）
    ctx.set_line_width(2.2)
    ctx.move_to(158 + TDX, ty(1))
    for k in range(1, 11):
        ctx.line_to((222 if k % 2 else 158) + TDX, ty(k) - TFH)
    ctx.stroke()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3.6)
    ctx.move_to(TX0, top)
    ctx.line_to(TX0, TY0)
    ctx.move_to(TX1, top)
    ctx.line_to(TX1, TY0)
    ctx.stroke()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    for k in range(1, 11):                                # 階の名前
        text(ctx, f"{k}階", TX0 - 10, ty(k) - TFH / 2, 36, RED if (flag_f is not None and abs(k - flag_f) < 0.5) else INK, align="right", alpha=a)
    for k in DEST_LIST:                                   # 棒
        u = rows_u.get(k, 0.0)
        if u <= 0.003:
            continue
        yk = ty(k)
        x = NORM[str(k)]
        for who, y_top, col, secs in (("st", yk - 54, SUMI, x["med_st_u"]), ("el", yk - 31, BLUE, x["med_el_u"])):
            al = a * u * (1.0 if hi in (None, who) else 0.3)
            ctx.set_source_rgba(*hexrgb(col, 0.92 * al))
            rrect(ctx, BAR_X0, y_top, secs * BAR_PX * ease(u), 20, 5)
            ctx.fill()
    if flag_f is not None:                                # 旗（行き先）
        fy = ty(1) - (flag_f - 1) * TFH
        _line(ctx, 262 + TDX, fy, 262 + TDX, fy - 50, 3, a=0.9 * a)
        ctx.move_to(262 + TDX, fy - 50)
        ctx.line_to(288 + TDX, fy - 42)
        ctx.line_to(262 + TDX, fy - 34)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(RED, 0.9 * a))
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(RED, 0.16 * a))        # 行き先の行
        ctx.rectangle(44, fy - TFH, 896, TFH)
        ctx.fill()


def tall_axis(ctx, a):
    """棒の目盛り（60秒・120秒）"""
    for sec in (60, 120):
        x = BAR_X0 + sec * BAR_PX
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.5 * a))
        ctx.set_line_width(1.8)
        ctx.set_dash([6, 6])
        ctx.move_to(x, ty(11) + 40)
        ctx.line_to(x, TY0 + 4)
        ctx.stroke()
        ctx.set_dash([])
        text(ctx, f"{sec}秒", x, 912, 36, PENCIL_T, alpha=a, bold=False)


def L_c2(ctx, t):
    a = fade(t, S("ch2") + 0.2, 0.4)
    t_run0, t_run1 = S("c2_2") + 0.2, E("c2_2") - 0.2          # 行き先を上へ（棒が出る）
    t_g0, t_g1 = S("g2") + 0.2, E("g2") - 0.5                  # 無音: グラフが右へ。旗もいっしょに上がる
    rows_u = {}
    for k in DEST_LIST:
        tk = lerp(t_run0, t_run1, (k - 2) / 8)
        rows_u[k] = clamp01((t - tk) / 0.5)
    if t < t_run0:
        flag_f = 2.0
        rows_u = {}
    elif t < t_run1:
        flag_f = 2.0 + 8.0 * clamp01((t - t_run0) / (t_run1 - t_run0))
    elif t < t_g0:
        flag_f = 10.0
    elif t < E("g2"):
        flag_f = 2.0 + 8.0 * ease(clamp01((t - t_g0) / (t_g1 - t_g0)))
    else:
        flag_f = lerp(10.0, float(TOP_UP), ease(clamp01((t - S("c2_6")) / 0.8)))
    if t < t_run0:
        rows_u = {}
    hi = None
    if S("c2_3") <= t < S("c2_4"):
        hi = "st"
    elif S("c2_4") <= t < S("c2_4b"):                  # v3: c2_4（あまり増えない）と c2_4c（待つ時間とドア）の間だけ。c2_4b（グラフにする）では外す
        hi = "el"
    text(ctx, "着くまでの時間（真ん中の値）", 100, 62, 44, INK, align="left", alpha=a)
    legend_sq(ctx, [(SUMI, "階段"), (BLUE, "エレベーター")], 300, 122, a=a)
    draw_tall(ctx, a, flag_f if t >= S("c2_2") - 0.3 else None, rows_u, hi)
    tall_axis(ctx, a * fade(t, t_run0, 0.4))
    if t >= S("c2_3") + 0.3 and t < S("c2_4"):
        tag(ctx, "階段は どんどん長く", 660, ty(8) - 20, 36, SUMI, fade(t, S("c2_3") + 0.3, 0.3))
    if t >= S("c2_4") + 0.3 and t < S("c2_4c"):
        tag(ctx, "エレベーターは あまり伸びない", 640, ty(1) - 36, 36, BLUE, fade(t, S("c2_4") + 0.3, 0.3))
    if t >= S("c2_4c") + 0.3 and t < S("c2_4b"):       # v3: 増えた文（c2_4c）に合わせた札
        tag(ctx, "ほとんどは 待つ・ドアの時間", 640, ty(1) - 36, 36, BLUE, fade(t, S("c2_4c") + 0.3, 0.3))
    if t >= S("c2_6") + 0.6:
        tag(ctx, f"分かれ目 {TOP_UP}階", 700, ty(TOP_UP) - 36, 40, RED, a * fade(t, S("c2_6") + 0.6, 0.3))


# ---------- 3章: 表示を見てから決める ----------
HALL_X0, HALL_X1 = 45.0, 600.0                      # 乗り場の壁（左ページの画面の座標）
DISP = (305.0, 175.0, 190.0, 120.0)                 # 階の表示窓（x, y, 幅, 高さ）
DOOR = (290.0, 330.0, 220.0, 550.0)                 # エレベーターのドア（x, y, 幅, 高さ）
BTN_C = (236.0, 585.0)                              # ボタンの中心
HALL_PX, HALL_PH = 124.0, DOOR[3] * 0.75           # 待つ人の足元の x と高さ（ドアの高さの 3/4。ボタンが肩〜胸の高さ）


def draw_hall(ctx, a, digit, mv, lamp, you_reach, big_hl=0.0):
    """乗り場の拡大: 壁・ドア・階の表示窓（ボタンの上・大きな数字）・ボタン・待つ人"""
    if a <= 0.003:
        return
    ctx.push_group()
    fill(ctx, hexrgb("#efe9da", 0.96))
    rrect(ctx, HALL_X0, 150, HALL_X1 - HALL_X0, 775, 10)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3.4)
    ctx.stroke()
    dx, dy, dw, dh = DOOR
    for k in range(2):                                   # ドア（2枚）
        fill(ctx, hexrgb("#b9c3d3", 0.98))
        ctx.rectangle(dx + k * dw / 2, dy, dw / 2, dh)
        ctx.fill_preserve()
        ctx.set_source_rgba(*hexrgb(INK, 0.85))
        ctx.set_line_width(2.8)
        ctx.stroke()
    sx, sy, sw, sh = DISP                                # 階の表示窓
    fill(ctx, (0.1, 0.12, 0.16, 1))
    rrect(ctx, sx, sy, sw, sh, 12)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.95))
    ctx.set_line_width(4)
    rrect(ctx, sx, sy, sw, sh, 12)
    ctx.stroke()
    bx, by = BTN_C                                       # ボタン（上向き・下向き）
    fill(ctx, (1, 1, 1, 0.97))
    rrect(ctx, bx - 28, by - 66, 56, 132, 12)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.85))
    ctx.set_line_width(2.8)
    ctx.stroke()
    for yy, up in ((by - 30, True), (by + 30, False)):
        ctx.set_source_rgba(*hexrgb(INK, 0.9))
        ctx.arc(bx, yy, 17, 0, 2 * math.pi)
        ctx.stroke()
        arrow_tri(ctx, bx, yy, up, 8, INK)
    if lamp:
        fill(ctx, hexrgb("#ff9f2e", 0.9))
        ctx.arc(bx, by - 30, 12, 0, 2 * math.pi)
        ctx.fill()
    draw_person(ctx, HALL_PX, 880.0, HALL_PH, BLUE, 0.0, amp=0.0, face=1, reach=you_reach)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    # 表示窓の数字（字）
    if digit is not None:
        text(ctx, digit, sx + sw / 2 - 14, sy + sh / 2 + 2, 96, "#ffd84d", alpha=a)
        if mv:
            ctx.push_group()
            arrow_tri(ctx, sx + sw - 34, sy + sh / 2, mv > 0, 16, "#ff6b5e")
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(a)
    if big_hl > 0.003:
        pen_circle(ctx, sx + sw / 2, sy + sh / 2, sw / 2 + 24, sh / 2 + 22, RED, seed=15, width=6, progress=big_hl, alpha=a)


def draw_mini_shaft(ctx, a, f_car, mv):
    """乗り場の拡大のとなりの、かごの場所（5階建て・かごの階が動く）"""
    if a <= 0.003:
        return
    x0, w = 690.0, 150.0
    ys = lambda f: 880.0 - (f - 1) * 125.0
    ctx.push_group()
    fill(ctx, hexrgb(SHAFT, 0.95))
    ctx.rectangle(x0, ys(5) - 100, w, 880 - ys(5) + 100)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(INK, 0.8))
    ctx.set_line_width(2.6)
    ctx.rectangle(x0, ys(5) - 100, w, 880 - ys(5) + 100)
    ctx.stroke()
    for k in range(1, 5):
        ctx.set_source_rgba(*hexrgb(INK, 0.35))
        ctx.set_line_width(2)
        ctx.move_to(x0, ys(k + 1))
        ctx.line_to(x0 + w, ys(k + 1))
        ctx.stroke()
    cy = ys(f_car)
    fill(ctx, hexrgb(CARC))
    ctx.rectangle(x0 + 20, cy - 96, w - 40, 96)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3.2)
    ctx.stroke()
    if mv:
        arrow_tri(ctx, x0 + w / 2, cy - 48, mv > 0, 14, RED)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    text(ctx, "かごの場所", x0 + w / 2, 126, 36, INK, alpha=a)


def hall_demo(t, t0):
    """乗り場の拡大の見本: かごが5階から1階まで下りてきて、止まり、また上がる（7秒でくり返し）。返り値: (かごの階, 向き)"""
    c = (t - t0) % 7.0
    if c < 0.8:
        return 5.0, 0
    if c < 4.8:
        return 5.0 - 4.0 * ease((c - 0.8) / 4.0), -1
    if c < 5.6:
        return 1.0, 0
    if c < 6.6:
        return 1.0 + 0.0, 0
    return 1.0, 0


def draw_choice(ctx, a, t):
    """決めごと: 表示が「1」ならエレベーター・それ以外なら階段（c3_3）"""
    if a <= 0.003:
        return
    for i, (digit, who, col, y) in enumerate((("1", "エレベーターで行く", BLUE, 300), ("ほかの階", "階段で行く", SUMI, 600))):
        u = a * fade(t, S("c3_3") + 0.4 + 1.2 * i, 0.4)
        if u <= 0.003:
            continue
        ctx.push_group()
        fill(ctx, (0.1, 0.12, 0.16, 1))
        rrect(ctx, 665, y - 100, 190, 130, 12)
        ctx.fill()
        ctx.set_source_rgba(*hexrgb(INK, 0.95))
        ctx.set_line_width(4)
        rrect(ctx, 665, y - 100, 190, 130, 12)
        ctx.stroke()
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(u)
        if i == 0:
            text(ctx, digit, 760, y - 33, 100, "#ffd84d", alpha=u)
        else:
            text(ctx, digit, 760, y - 33, 40, "#ffd84d", alpha=u)
        tag(ctx, who, 745, y + 58, 36, col, u)
        pen_line(ctx, 626, y - 36, 659, y - 36, col, seed=30 + i, width=6, progress=1.0, alpha=u)


def L_ch3(ctx, t):
    a = fade(t, S("ch3") + 0.2, 0.4)
    t_race = S("g3") - 0.15
    a_hall = a * out_fade(t, t_race, 0.4)
    a_race = fade(t, t_race, 0.4)
    if a_hall > 0.003:
        t_demo = S("c3_1")
        if t < t_demo:                                    # c3_0: 表示は止まっている（かごは 1階）
            f, mv = 1.0, 0
        else:
            f, mv = hall_demo(t, t_demo + 0.3)
        digit = f"{int(round(f))}"
        lamp = (t >= t_demo + 0.2) and (mv != 0 or f < 1.5)
        reach = math.sin(math.pi * clamp01((t - t_demo - 0.3) / 0.8)) if t >= t_demo else 0.0
        hl = clamp01((t - S("c3_1") - 1.2) / 0.5) * out_fade(t, S("c3_3") - 0.2, 0.3)
        draw_hall(ctx, a_hall, digit, mv, lamp, reach, hl)
        a_ms = a_hall * out_fade(t, S("c3_3") - 0.1, 0.3) * fade(t, S("c3_1") + 0.2, 0.4)
        draw_mini_shaft(ctx, a_ms, f, mv)
        tag(ctx, "表示 ＝ かごの今の階", 330, 108, 40, RED, a_hall * fade(t, S("c3_1") + 1.0, 0.4) * out_fade(t, S("c3_3") - 0.1, 0.3))
        draw_choice(ctx, a_hall, t)
    if a_race > 0.003:
        draw_scene(ctx, SC3, t, TM3, a_race, people=1.0, flags=1.0, st_alpha=0.5)
        legend_people(ctx, a_race, items=((BLUE, "表示を見て決める人"), ("#9aa1b3", "いつも階段の人")))
        cam = SC3.cam
        if t >= S("g3") + 0.1:
            pen_circle(ctx, cam.sx(BTN_X - 6), cam.sy(floor_y(1) - FH + 39), 52 * cam.SC + 6, 34 * cam.SC + 6, RED, seed=19, width=5,
                       progress=clamp01((t - S("g3") - 0.1) / 0.5), alpha=a_race * out_fade(t, S("g3") + 2.6, 0.4))
        draw_arrival_tags(ctx, SC3, t, TM3, a_race)


# ---------- 4章: 朝の混雑 ----------
def L_ch4(ctx, t):
    a = fade(t, S("ch4") + 0.2, 0.4)
    draw_scene(ctx, SC4, t, TM4, a, people=1.0, flags=1.0)
    legend_people(ctx, a, y=152, items=((SUMI, "階段の人"), (BLUE, "エレベーターの人"), (GRAY_P, "かごのほかの人")))
    draw_arrival_tags(ctx, SC4, t, TM4, a)


# ---------- 5章: 下り（階段は上りの約1.3倍の速さ。くり返しのイメージ。同じ階段を、上る人と下りる人が同時にスタート） ----------
DOWN_SC = Sc.__new__(Sc)                              # 5階建ての断面（階段の動きだけ使う）
DOWN_SC.n, DOWN_SC.D, DOWN_SC.p, DOWN_SC.T_st = 5, 5, SC0.p, 1.0
DOWN_SC.stair_flights = 2 * (5 - 1)
DOWN_SC.cam = Cam(5)
DOWN_X = sum(DOWN_RATIO) / 2                         # 下りは上りの 1.2〜1.45倍（真ん中 1.325 ＝ 約1.3倍）
DOWN_UP_SEC = 7.0                                    # 絵の上りにかける動画の秒（下りは 1/1.325）
DOWN_PER = 9.0


def draw_static_car(ctx, f):
    fill(ctx, hexrgb(CARC))
    cy = floor_y(f)
    ctx.rectangle(CAR_X0, cy - CAR_H, CAR_X1 - CAR_X0, CAR_H)
    ctx.fill_preserve()
    ctx.set_source_rgba(*hexrgb(INK, 0.9))
    ctx.set_line_width(3.2)
    ctx.stroke()


def draw_down(ctx, t, a, t0):
    """階段を上る人（うすい色）と下りる人（墨）が、同じ階段を同時にスタート。下りのほうが約1.3倍の速さ"""
    if a <= 0.003:
        return
    cam = DOWN_SC.cam
    c = (t - t0) % DOWN_PER
    ctx.push_group()
    ctx.save()
    cam.apply(ctx)
    draw_building(ctx, DOWN_SC, flags=1.0, flag_floor=1)
    draw_static_car(ctx, 5)
    u_up = clamp01(c / DOWN_UP_SEC)
    u_dn = clamp01(c / (DOWN_UP_SEC / DOWN_X))
    up = DOWN_SC.stair_state(u_up * 1.0)
    dn = DOWN_SC.stair_state(1.0 - u_dn)
    walk_up = 0.0 < u_up < 1.0
    walk_dn = 0.0 < u_dn < 1.0
    draw_person(ctx, up["x"] - 14, up["y"], P_H, "#9aa1b3", 2 * math.pi * 1.3 * t, 1.0 if walk_up else 0.0, face=up["face"],
                climb=1.0 if walk_up else 0.0, a=0.9)
    draw_person(ctx, dn["x"] + 18, dn["y"], P_H, SUMI, 2 * math.pi * 1.7 * t, 1.0 if walk_dn else 0.0, face=-dn["face"],
                climb=0.0, a=1.0)
    ctx.restore()
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    for k in range(1, 6):
        cam.text(ctx, f"{k}階", BX0 - 44, floor_y(k) - FH / 2, 40, RED if k == 1 else INK, alpha=a)


def L_ch5(ctx, t):
    a = fade(t, S("ch5") + 0.2, 0.4)
    text(ctx, "階段の速さ（くり返しのイメージ）", 100, 62, 44, INK, align="left", alpha=a)
    legend_sq(ctx, [("#9aa1b3", "上る人"), (SUMI, f"下りる人（約{SH['DOWN_X']}倍の速さ）")], 490, 124, a=a)
    draw_down(ctx, t, a, S("c5_1") - 0.3)


# ---------- まとめ ----------
def L_end(ctx, t):
    a = fade(t, S("ch6") + 0.2, 0.4)
    title_mark(ctx, t, S("ch6") - 10.0, a)
    draw_scene(ctx, SC0, t, STATIC, a, people=1.0, flags=1.0)
    legend_people(ctx, a)


LEFTS = [L_open, L_ch1, L_c2, L_ch3, L_ch4, L_ch5, L_end]


# ============================================================
# 右ページ（付箋・欄・折れ線グラフ・表。細かい数字は付箋と欄だけ。声は台本どおり）
# ============================================================
GPX0, GPX1 = 1170.0, 1780.0                         # グラフの横（行き先 2階〜10階）
GPY0, GPY1 = 384.0, 610.0                           # グラフの縦（100% 〜 0%）
COL_NORM, COL_RUSH, COL_DOWN = SUMI, ORANGE, GREEN


def gx(D):
    return GPX0 + (D - 2) / 8.0 * (GPX1 - GPX0)


def gy(p):
    return GPY1 - p * (GPY1 - GPY0)


def graph_axes(ctx, a):
    """折れ線グラフの軸: 横＝行き先の階（2〜10）・縦＝階段が先に着く割合。50% の横線"""
    if a <= 0.003:
        return
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.55 * a))
    ctx.set_line_width(2)
    for p in (0.0, 1.0):
        ctx.move_to(GPX0, gy(p))
        ctx.line_to(GPX1, gy(p))
        ctx.stroke()
    ctx.set_source_rgba(*hexrgb(RED, 0.7 * a))
    ctx.set_dash([10, 8])
    ctx.set_line_width(3)
    ctx.move_to(GPX0, gy(0.5))
    ctx.line_to(GPX1, gy(0.5))
    ctx.stroke()
    ctx.set_dash([])
    for p, lab in ((1.0, "100%"), (0.5, "50%"), (0.0, "0%")):
        text(ctx, lab, GPX0 - 14, gy(p), 36, RED if p == 0.5 else INK, align="right", alpha=a, bold=False)
    for D in DEST_LIST:
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.4 * a))
        ctx.set_line_width(1.6)
        ctx.move_to(gx(D), gy(0.0))
        ctx.line_to(gx(D), gy(0.0) + 8)
        ctx.stroke()
        text(ctx, f"{D}", gx(D), gy(0.0) + 30, 36, INK, alpha=a, bold=False)
    text(ctx, "横: 行き先の階　縦: 階段が先の割合", (GPX0 + GPX1) / 2 - 20, 680, 36, PENCIL_T, alpha=a, bold=False)


def graph_curve(ctx, vals, col, u, a=1.0, width=6):
    if u <= 0.003 or a <= 0.003:
        return
    pts = [(gx(D), gy(p)) for D, p in zip(DEST_LIST, vals)]
    xlim = GPX0 + clamp01(u) * (GPX1 - GPX0)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(width)
    ctx.move_to(*pts[0])
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x1 <= xlim + 1e-9:
            ctx.line_to(x1, y1)
        else:
            if x0 < xlim:
                f = (xlim - x0) / (x1 - x0)
                ctx.line_to(x0 + f * (x1 - x0), y0 + f * (y1 - y0))
            break
    ctx.stroke()
    for (x, y) in pts:
        if x <= xlim + 1e-9:
            ctx.arc(x, y, 6.5, 0, 2 * math.pi)
            ctx.fill()


def graph_legend(ctx, items, a):
    """凡例（線の色の見本と名前）"""
    x = RX
    for col, lab in items:
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.set_line_width(7)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        ctx.move_to(x, 332)
        ctx.line_to(x + 40, 332)
        ctx.stroke()
        text(ctx, lab, x + 52, 332, 36, INK, align="left", alpha=a)
        x += 52 + text_width(lab, 36) + 36


def pt_mark(ctx, D, p, label, t, t0, a=1.0, seed=3, dy=-56, dx=0):
    """分かれ目の点に赤丸と札"""
    if t < t0:
        return
    pen_circle(ctx, gx(D), gy(p), 24, 24, RED, seed=seed, width=5, progress=clamp01((t - t0) / 0.5), alpha=a)
    tag(ctx, label, gx(D) + dx, gy(p) + dy, 36, RED, a * fade(t, t0 + 0.3, 0.3))


def R_open(ctx, t):
    s2 = "階段が早い？"
    text(ctx, "何階まで、", RX, 175, 54, INK, align="left")
    text(ctx, s2, RX, 255, 60, INK, align="left")
    wr(ctx, f"{SC0.n}階建てのビル・エレベーター1台", RX, 350, 38, INK, S("c0_2") + 0.3, t, cps=11)
    wr(ctx, f"行き先は {SC0.D}階", RX, 408, 42, RED, S("c0_3") + 0.3, t, cps=11)
    ff = fade(t, TM0.tv[0], 0.25) * out_fade(t, E("g0") - 0.2, 0.3)
    if ff > 0.003:
        text(ctx, "▶▶ 早回し", RX, 482, 40, PENCIL_T, align="left", bold=False, alpha=ff)
    wr(ctx, "→ 階段の人が先に着いた", RX, 482, 42, RED, S("c0_6") + 0.3, t, cps=11)
    if t >= S("c0_6") + 0.2:
        pen_line(ctx, RX - 4, 298, RX + text_width(s2, 60) + 4, 294, RED, seed=7, width=6, progress=clamp01((t - S("c0_6") - 0.2) / 0.5))
    if t >= S("c0_8") + 0.3:
        mini_sticky(ctx, "何階まで、階段が早い？", RX, 575, 40, "yellow", a=fade(t, S("c0_8") + 0.3), align="left", tilt=-0.015)
    if t >= S("c0_9") + 0.3:
        mini_sticky(ctx, "あなたは、何階まで階段派？", RX, 660, 40, "blue", a=fade(t, S("c0_9") + 0.3), align="left", tilt=0.015)
    if t >= S("c0_10") + 0.3:
        mini_sticky(ctx, "この動画：階段とエレベーターを\n1万回ずつ競わせて、分かれ目の階を確かめる", RX, 790, 38, "mint",
                    a=fade(t, S("c0_10") + 0.3), align="left", tilt=-0.01)


def R_ch1(ctx, t):
    a = out_fade(t, S("c1_11") - 0.2, 0.3)
    if a > 0.003:
        if t >= S("c1_1") + 0.3:
            mini_sticky(ctx, f"{SH['FL_LO']}〜{SH['FL_HI']}階建て・エレベーター1台", RX, 150, 40, "yellow", a=a * fade(t, S("c1_1") + 0.3), align="left", tilt=-0.015)
        if t >= S("c1_2") + 0.3:
            mini_sticky(ctx, f"階段 1秒に高さ約{SH['CM24']}cm", RX, 235, 40, "blue", a=a * fade(t, S("c1_2") + 0.3), align="left", tilt=0.012)
        if t >= S("c1_3") + 0.3:
            mini_sticky(ctx, "かご ＝ 人が乗る箱", RX, 320, 40, "pink", fg=RED, a=a * fade(t, S("c1_3") + 0.3), align="left", tilt=-0.012)
        if t >= S("c1_8") + 0.3:
            mini_sticky(ctx, f"差の真ん中 {SH['GAP5']}秒", RX, 405, 40, "mint", a=a * fade(t, S("c1_8") + 0.3), align="left", tilt=0.012)
        if t >= S("c1_9") + 0.3:
            mini_sticky(ctx, f"かごが1階 → 階段が先 {SH['S1_9']}%", RX, 490, 40, "yellow", a=a * fade(t, S("c1_9") + 0.3), align="left", tilt=-0.012)
    if t >= S("c1_12") + 0.4:
        sticky(ctx, f"{SMP['open3']['dest']}階までなら\n階段のほうが 少しだけ先に着く回が多い", RCX, 560, 38, "pink", fg=RED, a=fade(t, S("c1_12") + 0.4), tilt=-0.015)


def graph_block(ctx, t, a_axes, normal_u, normal_a=1.0, extra=None):
    graph_axes(ctx, a_axes)
    graph_curve(ctx, PU, COL_NORM, normal_u, normal_a * a_axes)
    if extra:
        extra(ctx)


def R_c2(ctx, t):
    hdr = out_fade(t, S("c2_9") - 0.2, 0.3)
    if hdr > 0.003:
        if t >= S("c2_2") + 0.3:
            mini_sticky(ctx, "2階〜10階 各1万回", RX, 150, 40, "yellow", a=hdr * fade(t, S("c2_2") + 0.3), align="left", tilt=-0.015)
        if t >= S("c2_5") + 0.1:
            mini_sticky(ctx, "分かれ目 ＝ 階段が先の回が多い、\nいちばん上の階", RX, 248, 38, "pink", fg=RED, a=hdr * fade(t, S("c2_5") + 0.1), align="left", tilt=0.012)
    a_ax = fade(t, S("c2_4b") + 0.3, 0.4)                # v3: 「グラフにしていきます」（c2_4b）で軸が出る
    u = clamp01((t - (S("g2") + 0.2)) / (dur("g2") - 0.7))
    graph_legend(ctx, [(COL_NORM, "ふだん（上り）")], a_ax * hdr if t < S("c2_9") else a_ax)
    graph_axes(ctx, a_ax)
    graph_curve(ctx, PU, COL_NORM, u, a_ax)
    pr3 = PU[1]
    pt_mark(ctx, 3, pr3, f"{TOP_UP}階 {SH['P3']}%", t, S("c2_6") + 0.2, dx=62, dy=-52)
    if t >= S("c2_7") + 0.3:
        ma = fade(t, S("c2_7") + 0.3)
        lab4 = f"4階 {SH['P4']}%"
        cx4, cy4 = gx(4) + 170, gy(PU[2]) - 62
        pen_line(ctx, gx(4) + 8, gy(PU[2]) - 6, cx4 - (text_width(lab4, 40) + 44) / 2 + 6, cy4 + 26, PENCIL, seed=4, width=3, progress=1.0, alpha=ma)
        mini_sticky(ctx, lab4, cx4, cy4, 40, "blue", a=ma, tilt=0.02)
    if t >= S("c2_8") + 0.3:
        ma = fade(t, S("c2_8") + 0.3)
        lab10 = f"10階 {SH['P10']}%"
        cx10, cy10 = gx(10) - 150, gy(PU[8]) - 78
        pen_line(ctx, gx(10) - 8, gy(PU[8]) - 10, cx10 + (text_width(lab10, 40) + 44) / 2 - 10, cy10 + 30, PENCIL, seed=5, width=3, progress=1.0, alpha=ma)
        mini_sticky(ctx, lab10, cx10, cy10, 40, "yellow", a=ma, tilt=-0.02)
    if t >= S("c2_10") + 0.4:
        sticky(ctx, f"ふだんのビルでは\n分かれ目は {TOP_UP}階", RCX, 215, 42, "pink", fg=RED, a=fade(t, S("c2_10") + 0.4), tilt=-0.015)


# ---------- 3章の表 ----------
TBL_X = (1290.0, 1490.0, 1690.0)
TBL_Y0 = 440.0
TBL_DY = 72.0
TBL_HEAD = ("表示を見て\n決める", "いつも\n階段", "いつも\nエレベーター")


def R_ch3(ctx, t):
    a1 = out_fade(t, S("c3_9") - 0.2, 0.3)
    if t >= S("c3_3") + 0.3 and a1 > 0.003:
        mini_sticky(ctx, "1階にいれば エレベーター\nいなければ 階段", RX, 190, 40, "yellow", a=a1 * fade(t, S("c3_3") + 0.3), align="left", tilt=-0.015)
    t_tab = S("c3_4") + 0.2
    ta = fade(t, t_tab, 0.4)
    if ta > 0.003:
        for x, h in zip(TBL_X, TBL_HEAD):
            text(ctx, h, x, 330, 36, INK, alpha=ta, bold=False)
        ctx.set_source_rgba(*hexrgb(PENCIL, 0.6 * ta))
        ctx.set_line_width(2)
        ctx.move_to(RX, 388)
        ctx.line_to(1830, 388)
        ctx.stroke()
    reveal = {3: S("c3_4") + 0.4, 4: S("c3_4") + 0.9, 5: S("c3_6") + 0.3, 2: S("c3_8") + 0.3}
    circ = {3: mid("c3_4", 0.8), 4: mid("c3_4", 0.95), 5: S("c3_7") + 0.3, 2: S("c3_8") + 1.0}
    for i, D in enumerate(LOOK_ROWS):
        tr = reveal[D]
        if t < tr:
            continue
        ra = fade(t, tr, 0.35)
        y = TBL_Y0 + i * TBL_DY
        vals = look_row(D)
        x_ = NORM[str(D)]
        raw = (x_["mean_look"], x_["mean_st"], x_["mean_el"])
        best = int(np.argmin(raw))
        text(ctx, f"{D}階", RX + 50, y, 42, INK, alpha=ra)
        for j, (cx, v) in enumerate(zip(TBL_X, vals)):
            text(ctx, f"{v}秒", cx, y, 44, RED if (j == best and best == 0) else INK, alpha=ra)
        if t >= circ[D]:
            cx = TBL_X[best]
            col = RED if best == 0 else PENCIL
            pen_circle(ctx, cx, y, 70, 28, col, seed=40 + D, width=5, progress=clamp01((t - circ[D]) / 0.5), alpha=ra)
    if t >= S("c3_10") + 0.4:
        sticky(ctx, f"表示を見て決めるのが得なのは\n{TOP_UP}階と{TOP_UP + 1}階だけ", RCX, 200, 38, "pink", fg=RED,
               a=fade(t, S("c3_10") + 0.4), tilt=-0.015)


def R_c4(ctx, t):
    hdr = out_fade(t, S("c4_7") - 0.2, 0.3)
    if hdr > 0.003:
        if t >= S("c4_2") + 0.3:
            mini_sticky(ctx, f"ほかの人を運んでいる {SH['RUSH_BUSY']}割", RX, 150, 40, "yellow", a=hdr * fade(t, S("c4_2") + 0.3), align="left", tilt=-0.015)
        if t >= S("c4_3") + 0.3:
            mini_sticky(ctx, f"途中の階で止まる {SH['RUSH_STOP']}割", RX, 235, 40, "blue", a=hdr * fade(t, S("c4_3") + 0.3), align="left", tilt=0.012)
    a_ax = fade(t, S("c4_3") + 0.5, 0.4)
    u = clamp01((t - (S("g4") + 0.2)) / (dur("g4") - 0.6))
    graph_legend(ctx, [(COL_NORM, "ふだん"), (COL_RUSH, "朝の混雑")], a_ax)
    graph_axes(ctx, a_ax)
    graph_curve(ctx, PU, COL_NORM, 1.0, a_ax)
    graph_curve(ctx, PR, COL_RUSH, u, a_ax)
    pt_mark(ctx, TOP_RUSH, PR[TOP_RUSH - 2], f"{TOP_RUSH}階 {SH['R7']}%", t, S("c4_4") + 0.2, seed=6, dy=-54, dx=0)
    if t >= S("c4_8") + 0.4:
        sticky(ctx, f"エレベーターが混む朝は\n分かれ目が ずっと上の階", RCX, 215, 40, "pink", fg=RED, a=fade(t, S("c4_8") + 0.4), tilt=-0.015)


def R_c5(ctx, t):
    hdr = out_fade(t, S("c5_5") - 0.2, 0.3)
    if hdr > 0.003:
        if t >= S("c5_1") + 0.3:
            mini_sticky(ctx, f"下りは 上りの約{SH['DOWN_X']}倍の速さ", RX, 150, 40, "yellow", a=hdr * fade(t, S("c5_1") + 0.3), align="left", tilt=-0.015)
        if t >= S("c5_2") + 0.3:
            mini_sticky(ctx, "エレベーターは 上りも下りも ほぼ同じ", RX, 235, 38, "blue", a=hdr * fade(t, S("c5_2") + 0.3), align="left", tilt=0.012)
    a_ax = fade(t, S("ch5") + 0.5, 0.4)
    u = clamp01((t - (S("g5") + 0.2)) / (dur("g5") - 0.6))
    graph_legend(ctx, [(COL_NORM, "上り（ふだん）"), (COL_DOWN, "下り")], a_ax)
    graph_axes(ctx, a_ax)
    graph_curve(ctx, PU, COL_NORM, 1.0, a_ax)
    graph_curve(ctx, PD, COL_DOWN, u, a_ax)
    pt_mark(ctx, TOP_DOWN, PD[TOP_DOWN - 2], f"{TOP_DOWN}階から下りる {SH['D5']}%", t, S("c5_3") + 0.2, seed=7, dy=-54, dx=-30)
    if t >= S("c5_6") + 0.4:
        sticky(ctx, f"下りなら\n分かれ目は {TOP_DOWN}階", RCX, 215, 40, "pink", fg=RED, a=fade(t, S("c5_6") + 0.4), tilt=-0.015)


def R_end(ctx, t):
    if t >= S("c6_1") + 0.3:
        mini_sticky(ctx, f"ふだん（上り）　分かれ目は {TOP_UP}階", RX, 150, 40, "yellow", a=fade(t, S("c6_1") + 0.3), align="left", tilt=-0.012)
    if t >= S("c6_2") + 0.3:
        mini_sticky(ctx, "3階と4階なら 表示を見て決める", RX, 240, 40, "blue", a=fade(t, S("c6_2") + 0.3), align="left", tilt=0.012)
    if t >= S("c6_3") + 0.3:
        mini_sticky(ctx, f"朝の混雑　分かれ目は {TOP_RUSH}階", RX, 330, 40, "pink", fg=RED, a=fade(t, S("c6_3") + 0.3), align="left", tilt=-0.01)
    if t >= S("c6_4") + 0.3:
        mini_sticky(ctx, f"下り　分かれ目は {TOP_DOWN}階", RX, 420, 40, "mint", a=fade(t, S("c6_4") + 0.3), align="left", tilt=0.01)
    wr(ctx, "作り物のビル", RX, 520, 38, PENCIL_T, S("c6_5") + 0.3, t, bold=False, cps=12)
    wr(ctx, "疲れて遅くなることは考えない", RX, 580, 38, PENCIL_T, S("c6_6") + 0.3, t, bold=False, cps=14)


RIGHTS = [R_open, R_ch1, R_c2, R_ch3, R_c4, R_c5, R_end]


# ============================================================
# 右ページ下の欄（最初の答えから終了画面まで出しっぱなし。区切りの4秒だけ消える）
#   cells は (ラベル, 値, 色, 現れる時刻) のリスト。1〜3つ並べる。dim は「直前の値を薄く残す」
# ============================================================
NB = (1030, 706, 1830, 916)
BOX_DIM = 0.4


def box_keys():
    p = lambda v: f"{v}%"
    K = lambda t, cap, cells, dim=False, circle=None: dict(t=t, cap=cap, cells=cells, dim=dim, circle=circle)
    M = lambda lab, val, col=INK, rev=None: (lab, val, col, rev)
    c3 = "上り・3階まで・1万回ずつ"
    a3 = M("階段が先", p(SH["P3"]), RED)
    cu = "ふだんの上り"
    bu = M("分かれ目", f"{TOP_UP}階", RED)
    lk = "3階までの平均（表示を見て決める）"
    l1 = M("表示を見て決める", f"{look_row(3)[0]}秒", RED)
    l2 = M("いつも階段", f"{look_row(3)[1]}秒", INK)
    cr = "朝の混雑"
    br = M("分かれ目", f"{TOP_RUSH}階", RED)
    r7 = M(f"{TOP_RUSH}階で階段が先", p(SH["R7"]), RED)
    cd = "下り"
    bd = M("分かれ目", f"{TOP_DOWN}階", RED)
    d5 = M(f"{TOP_DOWN}階から下りて階段が先", p(SH["D5"]), RED)
    return [
        K(mid("c1_7", 0.6), c3, [a3], circle=0),
        K(S("ch2") + 0.5, c3, [a3], dim=True),
        K(mid("c2_6", 0.6), cu, [bu], circle=0),
        K(S("ch3") + 0.5, cu, [bu], dim=True),
        K(mid("c3_4", 0.7), lk, [l1, l2], circle=0),
        K(S("ch4") + 0.5, lk, [l1, l2], dim=True),
        K(mid("c4_4", 0.6), cr, [br], circle=0),
        K(mid("c4_5", 0.6), cr, [r7], circle=0),
        K(S("ch5") + 0.5, cr, [r7], dim=True),
        K(mid("c5_3", 0.6), cd, [bd], circle=0),
        K(mid("c5_4", 0.6), cd, [d5], circle=0),
        K(S("ch6") + 0.5, "分かれ目（階段が先の回が多い、いちばん上）",
          [M("ふだん", f"{TOP_UP}階", INK), M("朝の混雑", f"{TOP_RUSH}階", RED), M("下り", f"{TOP_DOWN}階", INK)]),
    ]


def _cell_xs(n):
    x0, x1 = NB[0], NB[2]
    return [x0 + (x1 - x0) * (i + 0.5) / n for i in range(n)]


def _key_cells(ctx, key, a, t, tk, pop):
    x0, y0, x1, y1 = NB
    n = len(key["cells"])
    for (lab, val, col, rev), cx in zip(key["cells"], _cell_xs(n)):
        ra = 1.0 if rev is None else fade(t, rev, 0.4)
        if ra <= 0.003:
            continue
        text(ctx, lab, cx, y0 + 98, 36, col, alpha=a * ra)
        sc = 1 + (0.25 * (1 - ease_out(clamp01((t - tk) / 0.3))) if pop else 0.0)
        ctx.save()
        ctx.translate(cx, y0 + 162)
        ctx.scale(sc, sc)
        text(ctx, val, 0, 0, 68, col, alpha=a * ra)
        ctx.restore()


def draw_box(ctx, t):
    keys = box_keys()
    t0 = keys[0]["t"]
    if t < t0 - 0.1:
        return
    a = fade(t, t0 - 0.1, 0.3)
    i = max([k for k, kk in enumerate(keys) if kk["t"] <= t + 0.1] or [0])
    cur = keys[i]
    prev = keys[i - 1] if i > 0 else None
    tk = cur["t"]
    u = fade(t, tk, 0.35)
    dimv = lambda k: BOX_DIM if k["dim"] else 1.0
    x0, y0, x1, y1 = NB
    ctx.set_source_rgba(1, 1, 1, 0.6 * a)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.fill()
    ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a))
    ctx.set_line_width(3)
    rrect(ctx, x0, y0, x1 - x0, y1 - y0, 16)
    ctx.stroke()
    ctx.set_line_width(2)
    for kk, vis in ((cur, u), (prev, 1 - u)):
        if kk is None or vis <= 0.01:
            continue
        n = len(kk["cells"])
        if n >= 2:
            for j in range(1, n):
                xx = x0 + (x1 - x0) * j / n
                ctx.set_source_rgba(*hexrgb(PENCIL, 0.7 * a * (1.0 if kk is cur else vis)))
                ctx.move_to(xx, y0 + 70)
                ctx.line_to(xx, y1 - 18)
                ctx.stroke()
    cy_cap = y0 + 34
    va_a = dimv(cur) * u + (dimv(prev) if prev else 1.0) * (1 - u)
    if prev is None or prev["cap"] == cur["cap"]:
        text(ctx, cur["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * va_a)
    else:
        text(ctx, cur["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * u * dimv(cur))
        text(ctx, prev["cap"], (x0 + x1) / 2, cy_cap, 36, PENCIL_T, bold=False, alpha=a * (1 - u) * dimv(prev))
    same = prev is not None and prev["cells"] == cur["cells"]
    if prev is None or same:
        _key_cells(ctx, cur, a * va_a, t, tk, False)
    else:
        _key_cells(ctx, prev, a * (1 - u) * dimv(prev), t, tk, False)
        _key_cells(ctx, cur, a * u * dimv(cur), t, tk, True)
    if cur["circle"] is not None and not cur["dim"]:
        n = len(cur["cells"])
        cx = _cell_xs(n)[cur["circle"]]
        pen_circle(ctx, cx, y0 + 162, 118 if n == 1 else 100, 44, RED, seed=121, width=6, progress=clamp01((t - tk - 0.3) / 0.5), alpha=a)


# ============================================================
# 章の付箋・1万回の合図・終了画面・全体
# ============================================================
def T_ES():
    """終了画面の始まり（c6_6 を言い終わって 0.3秒後。v6: 最後の20秒に固定するのをやめた）"""
    return E("c6_6") + 0.3


BANNERS = lambda: [S("c1_6")]


END_SUB = "面白かったと思ってもらえたら\nチャンネル登録・高評価\nよろしくお願いします"       # 終了画面の付せん（v5・ユーザー指示）
LCX_E, RCX_E = 490, 1430                              # 終了画面: 左ページ・右ページの中央


def big_sticky(ctx, label, value, cx, cy, w, h, color, fg=INK, a=1.0, tilt=0.0, lsz=46, vsz=64):
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
    text(ctx, label, 0, -38, lsz, INK, alpha=a)
    text(ctx, value, 0, 34, vsz, fg, alpha=a)
    ctx.restore()


def end_screen(ctx, t):
    """終了画面。v5: ノートの大きさを使う（文字はページの中＝左 x 40〜940・右 x 980〜1880。のどをまたがない。字幕の帯 y>940 に入らない）。
    左ページ: 答え＋付せん4枚（幅800・文字は 名前46px／答え64px）。右ページ: 問いかけの付せん（68px）→ 亀（幅の約6割）＋チャンネル登録の付せん（3行・52px）"""
    t0 = T_ES()
    b = fade(t, t0 + 0.3, 0.4)
    text(ctx, "答え", LCX_E, 84, 84, INK, alpha=b)
    text(ctx, "階段とエレベーターを、1万回ずつ競わせたら", LCX_E, 162, 38, INK, bold=False, alpha=b)
    rows = [("ふだんの上り", f"分かれ目は {TOP_UP}階", "yellow", INK, -0.010),
            ("朝の混雑", f"分かれ目は {TOP_RUSH}階", "pink", RED, 0.008),
            ("下り", f"分かれ目は {TOP_DOWN}階", "mint", INK, -0.008),
            ("表示を見て決める", f"得なのは {TOP_UP}階・{TOP_UP + 1}階", "blue", INK, 0.010)]
    H_, GAP_, Y0_ = 163, 16, 206
    for k, (lab, val, col, fg, tilt) in enumerate(rows):
        big_sticky(ctx, lab, val, LCX_E, Y0_ + H_ / 2 + k * (H_ + GAP_), 800, H_, col, fg=fg, a=b, tilt=tilt)
    tq, t9 = S("c6_7") + 0.05, S("c6_8")
    if t >= tq:
        q = fade(t, tq, 0.35) * (1 - fade(t, t9 - 0.1, 0.3))
        if q > 0.003:
            sticky(ctx, "次にエレベーターの\n前に立ったら\nどうする？", RCX_E, 480, 68, "yellow", a=q, tilt=-0.02)
    if t >= t9:
        from engine.brand import turtle
        ctx.push_group()
        blink = 1.0 if 0.35 < (t - t9) % 3.2 < 0.45 else 0.0
        turtle(ctx, RCX_E - 23, 400, 1.0, blink=blink)   # v6: 1.25 → 1.0（大きすぎるとの指摘。約8割）
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(fade(t, t9 + 0.1, 0.4))
        sticky(ctx, END_SUB, RCX_E, 690, 52, "pink", fg=INK, a=fade(t, t9 + 0.3, 0.4), tilt=-0.015)


def overlays(ctx, t):
    ch = tl.chapter_at(t)
    if ch and ch[0] > 0:
        age = t - ch[1]
        if 0 <= age <= 2.0:
            a = clamp01(age / 0.35) * clamp01((2.0 - age) / 0.4)
            lf.chapter_card(ctx, ch[2], a, size=60)
    for tb in BANNERS():
        a = fade(t, tb - 0.1, 0.25) * out_fade(t, tb + 1.5, 0.35)
        if a > 0.003:
            note.banner(ctx, "1万回ためす", lf.GUTTER, 470, a=a, t_rel=t - tb)


def page(ctx, t, fns, idx, t0):
    age = t - t0
    if idx > 0 and age < 0.35:
        grp(ctx, 1 - age / 0.35, fns[idx - 1], t)
    fns[idx](ctx, t)


def pages(ctx, t):
    ch = tl.chapter_at(t)
    idx, t0 = (ch[0], ch[1]) if ch else (0, 0.0)
    ctx.save()
    clip_left(ctx)
    page(ctx, t, LEFTS, idx, t0)
    ctx.restore()
    page(ctx, t, RIGHTS, idx, t0)
    draw_box(ctx, t)
    overlays(ctx, t)


# ============================================================
# 区切り（アイキャッチ。3章と4章の間・約4秒・声なし）。レジのロング（reji-long.py）と同じ形
#   左ページに「ここまで」＋左向きの赤い矢印＋ここまでのまとめ2行、右ページに「ここから」＋右向きの赤い矢印＋これから確かめること2行。
#   下で亀（まばたきつき）が左ページから右ページへ歩き、足あとの点が順に出る（点が出るたびに足音）。数字の欄はこの間は出さない
# ============================================================
EYE_LEFT = ("分かれ目は、", f"{TOP_UP}階")
EYE_RIGHT = ("朝の混雑なら？", "下りなら？")
EYE_LX, EYE_RX = 480, 1440                          # 左右のページの中央
EYE_Y = 860                                          # 亀の高さ
EYE_X0, EYE_X1 = 330.0, 1590.0                       # 亀が歩く範囲（左ページ → 右ページ）
FOOT_X0, FOOT_DX, FOOT_BEHIND = 260.0, 64.0, 70.0    # 足あとの点: 最初の位置・間隔・亀の中心からどれだけ後ろに出すか


def EYE0():
    return S("eye")


def EYE1():
    return E("eye")                                  # ＝ 4章の始まり


def eye_alpha(t):
    return fade(t, EYE0(), 0.3) * out_fade(t, EYE1(), 0.35)


def eye_x(t):
    return lerp(EYE_X0, EYE_X1, clamp01((t - EYE0()) / (EYE1() - EYE0())))


def foot_times():
    """足あとの点が出る時刻（亀の中心が点の FOOT_BEHIND 先を通ったとき）。足音もこの時刻に鳴らす"""
    out = []
    i = 0
    while True:
        px = FOOT_X0 + i * FOOT_DX
        u = (px + FOOT_BEHIND - EYE_X0) / (EYE_X1 - EYE_X0)
        if u > 1.0:
            break
        out.append((px, EYE0() + max(0.0, u) * (EYE1() - EYE0())))
        i += 1
    return out


def eye_arrow(ctx, x0, x1, y, color, seed, progress):
    pen_line(ctx, x0, y, x1, y, color, seed=seed, width=7, progress=progress)
    if progress >= 1:
        d = 1 if x1 > x0 else -1
        pen_line(ctx, x1, y, x1 - d * 34, y - 24, color, seed=seed + 1, width=7)
        pen_line(ctx, x1, y, x1 - d * 34, y + 24, color, seed=seed + 2, width=7)


def eye_page(ctx, t, cx, head, lines, back):
    a = fade(t, EYE0(), 0.5)                          # 最初の0.5秒で出し、最後まで出したまま
    w = text_width(head, 104)
    hand_title(ctx, head, cx - w / 2, 250, 104, seed=4 if back else 6, alpha=a)
    pr = clamp01((t - EYE0() - 0.1) / 0.4)
    if back:
        eye_arrow(ctx, cx + 210, cx - 230, 345, RED, 11, pr)
    else:
        eye_arrow(ctx, cx - 210, cx + 230, 345, RED, 21, pr)
    for i, s_ in enumerate(lines):
        text(ctx, s_, cx, 520 + i * 96, min(66, int(66 * 820 / text_width(s_, 66))), INK, alpha=a)


def eyecatch(ctx, t):
    from engine.brand import turtle
    lf.spread(ctx)
    eye_page(ctx, t, EYE_LX, "ここまで", EYE_LEFT, True)
    eye_page(ctx, t, EYE_RX, "ここから", EYE_RIGHT, False)
    for i, (px, tf) in enumerate(foot_times()):
        if t >= tf:
            ctx.set_source_rgba(0.25, 0.25, 0.3, 0.30 * fade(t, tf, 0.12))
            ctx.arc(px, EYE_Y + 18 + (7 if i % 2 else -7), 6, 0, 2 * math.pi)
            ctx.fill()
    blink = 1.0 if 0.35 < (t - EYE0()) % 1.8 < 0.47 else 0.0
    turtle(ctx, eye_x(t), EYE_Y - 3 * abs(math.sin((t - EYE0()) * 6.0)), 0.5, blink=blink)


def draw(ctx, t):
    lf.spread(ctx)
    tes = T_ES()
    ea = eye_alpha(t)
    if t < tes + 0.6 and ea < 0.997:
        grp(ctx, 1 - fade(t, tes, 0.5), pages, t)
    if t >= tes:
        end_screen(ctx, t)
    grp(ctx, ea, eyecatch, t)
    lf.subtitle(ctx, t, tl)


# ============================================================
# 音（BGM は 0秒から。足音・効果音はショートの作り方をコピー）
# ============================================================
def turtle_step(seed=0, high=False):
    """亀の足音（ぽてっ・とこっ）。短い下がり調子の丸い音＋ごく小さな擦れ"""
    tt = np.arange(int(core.SR * 0.14)) / core.SR
    f0 = (520.0 if high else 440.0) * (1 + 0.04 * np.random.default_rng(seed).uniform(-1, 1))
    f = f0 * (0.72 + 0.28 * np.exp(-tt * 40))
    tone = np.sin(2 * np.pi * np.cumsum(f) / core.SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / core.SR)
    env = np.minimum(1, tt * 900) * np.exp(-tt * 34)
    n = np.random.default_rng(seed + 50).standard_normal(len(tt))
    n = np.convolve(n, np.ones(12) / 12, mode="same") * np.exp(-tt * 120) * 0.35
    return (tone * env + n) * 0.8


def race_events():
    """見本の早回しで、かごが止まる（ドアが開く）時刻と、2人が着く時刻（動画の秒）。音を鳴らす所"""
    stops, arr = [], []
    for sc, tm in ((SC0, TM0), (SC3, TM3), (SC4, TM4)):
        for e in sc.log:
            if e[0] == "stop" and e[1] <= tm.tau[-1]:
                stops.append(tm.t_of(e[1]))
        arr += [tm.t_of(sc.T_st), tm.t_of(sc.T_el)]
    return sorted(stops), sorted(arr)


def build_audio():
    mx = lf.LongMixer(DUR)
    tl.add_voice(mx)
    mx.add(0, core.pad(DUR, freqs=(130.8, 196.0, 261.6, 329.6), vol=0.13), 1.0, bgm=True)
    mx.add(0.05, blip(659.3, 0.12), 0.3)
    for i in range(1, 7):
        mx.add(S(f"ch{i}"), whoosh(0.6), 0.3)
    stops, arr = race_events()
    for ts in stops:                                  # かごが止まってドアが開く: 小さな「ピン」
        mx.add(ts, tick(1500.0, 0.05), 0.12)
    for ta in arr:                                    # 着いた
        mx.add(ta, blip(659.3, 0.14), 0.3)
    for k, kk in enumerate(box_keys()):
        if k > 0 and not kk["dim"]:
            mx.add(kk["t"], bell(659.3 if k % 2 else 784.0, 1.0), 0.3)
    for tb in BANNERS():
        mx.add(tb - 0.4, riser(0.9), 0.45)
    for g in ("g0", "g1", "g2", "g3", "g4"):
        beat(mx, S(g) + 0.1, E(g) - 0.2, bpm=124, vol=0.22, accel=True)
        mx.add(S(g) + 0.2, shimmer(300, dur(g) - 0.5, seed=2), 0.3)
    mx.add(S("g5") + 0.2, shimmer(200, dur("g5") - 0.5, seed=5), 0.18)
    for cid in ("c1_11", "c2_9", "c3_9", "c4_7", "c5_5"):
        mx.add(S(cid) + 0.4, chord([392.0, 493.9, 587.3], 1.2), 0.3)
    mx.add(S("c6_7") + 0.05, chord([293.7, 370.0, 440.0], 1.6), 0.45)
    for i, (_px, tf) in enumerate(foot_times()):                      # 足あとの点が出るたびに足音
        mx.add(tf, turtle_step(seed=i, high=bool(i % 2)), 0.32)
    _i0, _i1 = int(EYE0() * core.SR), int(EYE1() * core.SR)           # この4秒は BGM を少し下げる（前後 0.3秒でなめらかに）
    _r = int(0.3 * core.SR)
    _g = np.ones(len(mx.bgm_buf))
    _g[_i0:_i1] = 0.55
    _g[max(0, _i0 - _r):_i0] = np.linspace(1, 0.55, _i0 - max(0, _i0 - _r))
    _g[_i1:_i1 + _r] = np.linspace(0.55, 1, len(_g[_i1:_i1 + _r]))
    mx.bgm_buf *= _g
    mx.add(S("c6_8") + 0.2, bell(523.3, 1.6), 0.3)
    return mx


# ============================================================
# 確認用の静止画の時刻
# ============================================================
def still_times():
    t_r0 = TM0.tv[0]
    ts = [0.0, 0.6, 2.0, S("c0_2") + 1.0, S("c0_3") + 1.2, S("c0_4") + 1.8, S("c0_5") + 1.0,
          t_r0 + 2.5, t_r0 + 5.0, t_r0 + 7.5, E("g0") - 0.3, mid("c0_6", 0.95), mid("c0_9", 0.95), mid("c0_10", 0.95),
          S("ch1") + 0.8, mid("c1_1", 0.9), mid("c1_2", 0.9), mid("c1_3", 0.95), mid("c1_4", 0.95), mid("c1_5", 0.97), S("c1_6") + 0.8,
          S("g1") + 1.5, S("g1") + 3.5, mid("c1_7", 0.95), mid("c1_8", 0.95), mid("c1_9", 0.95), mid("c1_10", 0.95), mid("c1_12", 0.95),
          S("ch2") + 0.8, mid("c2_2", 0.9), mid("c2_3", 0.95), mid("c2_4", 0.95), mid("c2_5", 0.95), S("g2") + 2.0, S("g2") + 4.0,
          mid("c2_6", 0.95), mid("c2_7", 0.95), mid("c2_8", 0.95), mid("c2_10", 0.95),
          S("ch3") + 0.8, mid("c3_0", 0.95), mid("c3_1", 0.4), mid("c3_1", 0.95), mid("c3_2", 0.95), mid("c3_3", 0.95),
          TM3.tv[0] + 1.0, TM3.tv[0] + 2.6, TM3.tv[0] + 4.2, E("g3") - 0.3,
          mid("c3_4", 0.95), mid("c3_6", 0.95), mid("c3_8", 0.95), mid("c3_10", 0.95),
          EYE0() + 0.6, EYE0() + 2.0, EYE1() - 0.3,
          S("ch4") + 0.8, mid("c4_2", 0.95), mid("c4_3", 0.95), TM4.tv[0] + 2.0, TM4.tv[0] + 4.0, TM4.tv[0] + 6.0, TM4.tv[0] + 8.0, E("g4") - 0.3,
          mid("c4_4", 0.95), mid("c4_5", 0.95), mid("c4_8", 0.95),
          S("ch5") + 0.8, mid("c5_1", 0.95), mid("c5_2", 0.95), S("g5") + 2.0, mid("c5_3", 0.95), mid("c5_4", 0.95), mid("c5_6", 0.95),
          S("ch6") + 0.8, mid("c6_2", 0.95), mid("c6_4", 0.95), mid("c6_6", 0.95),
          T_ES() + 1.0, mid("c6_7", 0.9), S("c6_8") + 1.5, DUR - 0.1]
    return sorted(set(round(x, 1) for x in ts if 0 <= x < DUR))


# ============================================================
# 文字起こし・読み・画面の文字（レジのロングと同じ形）
# ============================================================
def _ts(t):
    return f"{int(t // 60)}:{t % 60:04.1f}"


def stills_keep(draw_, times, out_dir, cols=4, thumb=(480, 270)):
    """lf.stills と同じ（静止画と sheet.png）。ただし前の still_*.png を消さない（このプロジェクトは削除しない決まり）"""
    from PIL import Image
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for tt in times:
        pth = out_dir / f"still_{tt:06.1f}.png"
        lf.still(draw_, tt, pth)
        paths.append(pth)
    ims = [Image.open(q).convert("RGB").resize(thumb, Image.LANCZOS) for q in paths]
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", ((thumb[0] + 8) * cols, (thumb[1] + 8) * rows), (60, 60, 60))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * (thumb[0] + 8), (i // cols) * (thumb[1] + 8)))
    sheet.save(out_dir / "sheet.png")
    print("一覧:", out_dir / "sheet.png")


GAP_NOTE = {
    "g0": "5階建てのビル（samples.open3）。ふたりが1階を出発。かごが上の階から下りてくる間に、階段の人が3階へ上る（階段が先）",
    "g1": "3階まで・1万回: マス目が埋まる（暗い色＝階段が先・青＝エレベーターが先。data.json と同じ乱数の1万回）",
    "g2": "行き先の階を2階から10階へ: 折れ線グラフが右へ描かれる（ふだんの上り）。左の旗もいっしょに上がる",
    "g3": "表示を見て決める・早回し（samples.look4_car1: かごは1階・エレベーターが先）。階段の人（うすい）はくらべるために同時に上る",
    "g4": "朝の混雑・早回し（samples.rush6: 6階・かごが人を乗せて途中の階で何度も止まる・階段が先）。右のグラフに朝の混雑の線が描かれる",
    "g5": "下り・くり返しのイメージ（同じ階段を、上る人と下りる人が同時にスタート）。右のグラフに下りの線が描かれる",
}


def write_transcript(path):
    rows = []
    for it in tl.items:
        if isinstance(it, lf.Chapter):
            rows.append("")
            if it.id == "ch0":
                rows.append(f"[章「{it.title}」（章カードなし。0秒目から題字「階段とエレベーター」と問い）]")
            else:
                rows.append(f"[章カード「{it.title}」]")
        elif isinstance(it, lf.Gap):
            s_, e_ = S(it.id), E(it.id)
            if it.id == "eye":
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・区切り。左「ここまで ← {''.join(EYE_LEFT)}」・"
                            f"右「ここから → {''.join(EYE_RIGHT)}」。亀が左ページから右ページへ歩く・足音。章ではない）")
            elif it.id in GAP_NOTE:
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.1f}秒・{GAP_NOTE[it.id]}）")
            else:
                rows.append(f"{_ts(s_)}〜{_ts(e_)} （ナレーションなし {e_ - s_:.0f}秒・映像だけ）")
        else:
            rows.append(f"{_ts(S(it.id))}〜{_ts(E(it.id))} 声＋字幕: {tl.clip(it.id).text}")
    rows.append("")
    rows.append(f"{_ts(T_ES())}〜{_ts(DUR)} 終了画面の区間（左右を空け、左ページに答え・問いかけ、右ページに亀と「チャンネル登録よろしく」）")
    path.write_text("\n".join(rows).lstrip("\n") + "\n", encoding="utf-8")
    print("文字起こし:", path)


def write_readings(path):
    from engine import voice
    rows = [f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）"]
    for t0_, title in tl.chapters:
        rows.append(f"  {lf._mmss(t0_)} {title}")
    for it in tl.items:
        if isinstance(it, lf.Line):
            shown_, spoken = split_reading(it.text)
            rows.append(f"{it.id}: {shown_}\n    → {voice.read_aloud(spoken)}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("読み:", path)


def scan(step=0.25, scale=0.25):
    """0.25秒ごとに描いて、画面の文字（字幕を除く）の位置と、描いた人の数を集める"""
    w, h = int(lf.W * scale), int(lf.H * scale)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    frames = []
    n = int(DUR / step)
    for i in range(n + 1):
        t = i * step
        core._LOG = []
        core._CUR_T = t
        DRAWN[0] = 0
        ctx = cairo.Context(surf)
        ctx.scale(scale, scale)
        draw(ctx, t)
        ents = [(e[1], e[2] / scale, e[3] / scale, e[4] / scale, e[5] / scale, e[6] / scale) for e in core._LOG]
        frames.append((t, ents, DRAWN[0]))
        core._LOG = None
    return frames


def write_screen_text(path, frames, step=0.25):
    seen = {}
    for t, ents, _n in frames:
        for e in ents:
            seen.setdefault(e[0], []).append(t)
    spans = []
    for s_, ts in seen.items():
        a = b = ts[0]
        for x in ts[1:] + [1e9]:
            if x - b > step * 1.5:
                spans.append((a, b + step, s_))
                a = x
            b = x
    spans.sort()
    rows = ["# 画面の文字（字幕を除く）と、見えている区間。0.25秒ごとに描いて調べた", ""]
    for a, b, s_ in spans:
        mark = "  ←短い" if b - a < 1.5 and not any(ch.isdigit() for ch in s_) else ""
        rows.append(f"{_ts(a)}〜{_ts(b)}（{b - a:4.1f}秒） {s_}{mark}")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print("画面の文字:", path)


OVERLAY_OK = set(CH_TITLES) | {"1万回ためす"}        # 章の付箋・1万回の合図は、わざと上に重ねている（不透明の付箋）


def overlaps(frames, step=0.25, need=3, shrink=3.0):
    """文字どうしの重なり（同じ2つの文字が need 回続けて＝0.5秒以上重なったら）"""
    runs, bad = {}, {}
    for t, ents, _n in frames:
        boxes = [(s_, x0 + shrink, y0 + shrink, x1 - shrink, y1 - shrink) for s_, x0, y0, x1, y1, *_r in ents if s_ not in OVERLAY_OK]
        hit = set()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if a[0] == b[0]:
                    continue
                w_ = min(a[3], b[3]) - max(a[1], b[1])
                h_ = min(a[4], b[4]) - max(a[2], b[2])
                if w_ > 0 and h_ > 0:
                    area = min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2]))
                    if w_ * h_ > 0.08 * area:
                        hit.add(tuple(sorted((a[0], b[0]))))
        for k in list(runs):
            if k not in hit:
                runs.pop(k)
        for k in hit:
            runs[k] = runs.get(k, 0) + 1
            if runs[k] >= need and k not in bad:
                bad[k] = t
    return bad


# ============================================================
# 場面の照合（声の数字・画面の数字・見本の早回し・文字の重なり・字幕・終了画面・長さ）
# ============================================================
# 「N回にM回」は1つの数字（割合）として数える
NUM_RE = r"\d+回に\d+回|\d[\d,]*万回|\d+[台列点秒分割倍つ個%階]|\d+"
FURN = _re.compile(r"^\d+階?$")                      # 建物の飾り（階の名前・階の表示窓の数字）。声の数字には数えない
MANY_OK = {                                         # 1文に声の数字が2つになる文（2026-10-19 ユーザーの直し「3階と4階では〜」。2つでひと組の階）
    "c3_4": "「3階と4階では、表示を見てから決めるのが」: ユーザーの直しの文。2つの階でひと組",
    "c3_10": "「3階と4階だけです」: 同上",
    "c6_2": "「3階と4階なら」: 同上",
}


def _sample_race_checks(sc, tm, name, first):
    """見本の早回し: かごの位置・ドアの開閉が log どおり、先に着く順が data.json（stairs・el_t）と一致"""
    out = []
    bad_pos, bad_door = 0, 0
    for ev in sc.log:
        k, t0, t1 = ev[0], ev[1], ev[2]
        tm_ = (t0 + t1) / 2
        pos, mv, doors = sc.car_state(tm_)
        if k == "wait":
            bad_pos += abs(pos - ev[3]) > 1e-9
            bad_door += bool(doors)
        elif k == "move":
            lo, hi = sorted((ev[3], ev[4]))
            bad_pos += not (lo < pos < hi) or mv != (1 if ev[4] > ev[3] else -1)
            bad_door += bool(doors)
        else:
            _, _, _, fl, o1, c0 = ev
            pos, mv, doors = sc.car_state(o1 + 1e-6 if c0 - o1 < 1e-6 else (o1 + c0) / 2)
            bad_pos += abs(pos - fl) > 1e-9 or mv != 0
            bad_door += not (abs(doors.get(fl, 0.0) - 1.0) < 1e-9 and len(doors) == 1)
    out.append((f"見本 {name}: かごの位置が log（wait/move/stop）どおり（食い違い {bad_pos}）", float(bad_pos == 0), 1, 0))
    out.append((f"見本 {name}: ドアの開閉が log どおり（止まりでは その階だけ全開・動いている間は全部閉じ。食い違い {bad_door}）", float(bad_door == 0), 1, 0))
    # 動き終わりの位置（log の目的の階）
    ends_ok = all(abs(sc.car_state(e[2] + 1e-6)[0] - e[4]) < 1e-9 for e in sc.log if e[0] == "move")
    out.append((f"見本 {name}: 動き終わりの位置 ＝ log の行き先の階", float(ends_ok), 1, 0))
    # 乗る・降りる: ドアが開いている間に
    b, f = sc.board, sc.final
    pos_b, _, d_b = sc.car_state(sc.t_board + 1e-3)
    pos_f, _, d_f = sc.car_state(f[4] + 1e-3)
    out.append((f"見本 {name}: 乗り始めと降り始めは、かごが その階にいてドアが全開",
                float(abs(pos_b - 1) < 1e-9 and d_b.get(1, 0) > 0.999 and abs(pos_f - sc.D) < 1e-9 and d_f.get(sc.D, 0) > 0.999), 1, 0))
    # 絵で2人が着く時刻（状態が done になる最初の時刻）と、data.json の stairs・el_t
    ts = np.arange(0.0, max(sc.T_st, sc.T_el) + 3.0, 0.01)
    st_done = next(x for x in ts if sc.stair_state(x)["done"])
    el_done = next(x for x in ts if sc.elev_state(x)["done"])
    out.append((f"見本 {name}: 階段の人が着く秒（絵）＝ data.json の stairs（0.01秒以内）", st_done, sc.T_st, 0.011))
    out.append((f"見本 {name}: エレベーターの人が着く秒（絵）＝ data.json の el_t（0.01秒以内）", el_done, sc.T_el, 0.011))
    got_first = "st" if st_done < el_done else "el"
    exp_first = "st" if SMP[sc.key]["stairs"] < SMP[sc.key]["el_t"] else "el"
    out.append((f"見本 {name}: 絵で先に着くのは {got_first}（data.json の stairs と el_t の順 ＝ {exp_first}。期待 {first}）",
                float(got_first == exp_first == first), 1, 0))
    t_s, t_e = arrival_times(sc, tm)
    out.append((f"見本 {name}: 早回しの時間の進みで、着く札の順も同じ（{'階段' if t_s < t_e else 'エレベーター'}が先）", float((t_s < t_e) == (first == "st")), 1, 0))
    out.append((f"見本 {name}: 早回しは2人が着いたあとまで続く", float(tm.tau[-1] > max(sc.T_st, sc.T_el)), 1, 0))
    return out


def scene_checks(frames=None):
    txt = lambda i: tl.clip(i).text
    n3 = NORM["3"]
    pu_s = {D: NORM[str(D)] for D in DEST_LIST}
    checks = [
        # ---- 画面と声の数字 = data.json（四捨五入）か閉じた式 ----
        ("1章「6割」・欄「60%」＝ normal.3.p_up（60.4%）の四捨五入", float(SH["P3"] == 60 and SH["P3W"] == 6), 1, 0),
        ("1章 マス目: 3階の1万回（data.json と同じ乱数）で階段が先の割合 ＝ normal.3.p_up", float(RUN3_FIRST_ST.mean()), n3["p_up"], 1e-12),
        ("1章 マス目（うすい色以外）: かごが1階にいた回で階段が先の割合 ＝ normal.3.p_up_s1", float(RUN3_FIRST_ST[RUN3_SCEN == 0].mean()), n3["p_up_s1"], 1e-12),
        ("1章 付箋「かごが1階 → 階段が先 9%」＝ p_up_s1 の四捨五入・「ほとんどエレベーターの勝ち」（15%未満）",
         float(SH["S1_9"] == 9 and n3["p_up_s1"] < 0.15), 1, 0),
        ("1章 付箋「差の真ん中 5秒」＝ gap_up（4.6秒）の四捨五入・「ほんの数秒」（1〜9秒）", float(SH["GAP5"] == 5 and 1 <= n3["gap_up"] < 10), 1, 0),
        ("1章 かごの場所「3割・3割・4割」＝ モデルの NORMAL.scen", float(SH["SCEN"] == (3, 3, 4)), 1, 0),
        ("1章 かごの場所: 1万回のうち実際の割合も 3割・3割・4割（±2%）",
         max(abs(float(np.mean(RUN3_SCEN == k)) - w) for k, w in enumerate(NORMAL["scen"])), 0.0, 0.02),
        ("1章 付箋「階段 1秒に高さ約24cm」＝ モデルの STAIR_MED（0.24 m/秒）", float(SH["CM24"] == 24 and STAIR_MED == 0.24), 1, 0),
        ("1章 付箋「5〜8階建て」＝ モデルの max(5, D)〜max(8, D+3)（D=3）。見本 open3 は5階建て",
         float(SH["FL_LO"] == 5 and SH["FL_HI"] == 8 and 5 <= SMP["open3"]["p"]["n"] <= 8), 1, 0),
        ("1章「エレベーターは、乗ってからは速いのですが、来るまでと、ドアに時間」: 見本 open3 の 動く時間 < 待つ＋ドア",
         float(time_parts(SC0)[2][1] < time_parts(SC0)[0][1] + time_parts(SC0)[1][1]), 1, 0),
        ("1章 時間の内わけの合計 ＝ el_t（見本 open3）", sum(x[1] for x in time_parts(SC0)), SC0.T_el, 1e-9),
        ("0章「階段の人のほうが、先に着きました」: 見本 open3 は 階段 < エレベーター", float(SC0.T_st < SC0.T_el), 1, 0),
        ("0章 声「3階」・見本 open3 の行き先 ＝ 3", SMP["open3"]["dest"], 3, 0),
        ("2章 行き先 2〜10階 ＝ モデルの DESTS", float(DEST_LIST == list(DESTS)), 1, 0),
        ("2章 分かれ目「3階」＝ 階段が先の割合が 50%以上の いちばん上の階（data.json）・別の乱数でも同じ",
         float(max(D for D in DEST_LIST if pu_s[D]["p_up"] >= 0.5) == TOP_UP == 3 and RES["top_up_normal_again"] == TOP_UP), 1, 0),
        ("2章 3階 60%（50%以上）・4階 40%（50%未満）", float(SH["P3"] == 60 and PU[1] >= 0.5 > PU[2] and SH["P4"] == 40), 1, 0),
        ("2章「10階では ほとんどありませんでした」: 付箋「10階 9%」は10%未満", float(SH["P10"] == 9 and PU[-1] < 0.10), 1, 0),
        ("2章「階段の時間は、どんどん長くなる」: 階段の真ん中の時間が行き先ごとにふえる",
         float(all(pu_s[a]["med_st_u"] < pu_s[b]["med_st_u"] for a, b in zip(DEST_LIST, DEST_LIST[1:]))), 1, 0),
        ("2章「エレベーターは あまり長くならない」: 2階→10階で 階段は 5倍以上・エレベーターは 3倍未満",
         float(pu_s[10]["med_st_u"] / pu_s[2]["med_st_u"] >= 5 and pu_s[10]["med_el_u"] / pu_s[2]["med_el_u"] < 3), 1, 0),
        ("2章 棒の長さの最大 ＝ 階段10階（131秒）が左ページに収まる（棒の右端 < 940）", BAR_X0 + pu_s[10]["med_st_u"] * BAR_PX, 0.0, 940.0),
    ]
    rows_ok = all((look_row(D)[0] < min(look_row(D)[1], look_row(D)[2])) for D in (TOP_UP, TOP_UP + 1))
    checks += [
        ("3章 表「3階・4階は 表示を見る が いちばん短い」（平均・data.json の生の値）",
         float(all(pu_s[D]["mean_look"] < min(pu_s[D]["mean_st"], pu_s[D]["mean_el"]) for D in (TOP_UP, TOP_UP + 1))), 1, 0),
        ("3章 表（四捨五入の値でも）3階・4階は 表示を見る が最小", float(rows_ok), 1, 0),
        ("3章「5階から上では、表示を見ても得をしない」: 5階〜10階は いつもエレベーター が 表示を見る より短い、5階が最初",
         float(all(pu_s[D]["mean_el"] < pu_s[D]["mean_look"] for D in DEST_LIST if D >= 5) and pu_s[TOP_UP + 1]["mean_el"] >= pu_s[TOP_UP + 1]["mean_look"]), 1, 0),
        ("3章「5階から上は、かごがどこにいても、エレベーターのほうが先に着く回が多い」: 5階〜10階の p_up_s1・p_up_s23 が50%未満",
         float(all(pu_s[D]["p_up_s1"] < 0.5 and pu_s[D]["p_up_s23"] < 0.5 for D in DEST_LIST if D >= 5)), 1, 0),
        ("3章「2階なら、表示を見るまでもなく階段」: 2階は いつも階段 が最短", float(pu_s[2]["mean_st"] < min(pu_s[2]["mean_look"], pu_s[2]["mean_el"])), 1, 0),
        ("3章 表の行 ＝ 3・4・5・2階（台本の順）", float(LOOK_ROWS == [3, 4, 5, 2]), 1, 0),
        ("3章 声「3階と、そのひとつ上の階」＝ 3階・4階（TOP_UP と TOP_UP+1）・「5階から上」＝ TOP_UP+2", float(TOP_UP == 3 and TOP_UP + 2 == 5), 1, 0),
        ("3章「かごが1階にいれば、待つ時間がほとんどない」: 見本 look4_car1 は かご1階・待ち 2秒未満",
         float(SMP["look4_car1"]["p"]["scen"] == 0 and SMP["look4_car1"]["el_wait"] < 2.0), 1, 0),
        ("3章 見本 look4_car1: エレベーターが先に着く（data.json）", float(SMP["look4_car1"]["el_t"] < SMP["look4_car1"]["stairs"]), 1, 0),
        ("4章 付箋「ほかの人を運んでいる 8割」＝ モデルの RUSH.scen[2]", float(SH["RUSH_BUSY"] == 8), 1, 0),
        ("4章 付箋「途中の階で止まる 3割」＝ モデルの RUSH.hall（0.30）", float(SH["RUSH_STOP"] == 3), 1, 0),
        ("4章 分かれ目「7階」＝ 朝の混雑で階段が先 50%以上の いちばん上の階・別の乱数でも（ふだんは3階）",
         float(max(D for D in DEST_LIST if RUSH_[str(D)]["p_up"] >= 0.5) == TOP_RUSH == 7 and TOP_RUSH > TOP_UP), 1, 0),
        ("4章 グラフ「7階 51%」＝ rush.7.p_up の四捨五入・「わずかに多いだけ」（50〜55%）", float(SH["R7"] == 51 and 0.50 <= RUSH_["7"]["p_up"] < 0.55), 1, 0),
        ("4章「混んだ朝は、思ったより上の階まで」: 朝の混雑の線は どの階でも ふだんより上", float(all(r > n for r, n in zip(PR, PU))), 1, 0),
        ("5章 付箋「下りは上りの約1.3倍の速さ」＝ モデルの DOWN_RATIO の真ん中（1.325）の四捨五入", float(SH["DOWN_X"] == 1.3 and DOWN_RATIO == (1.20, 1.45)), 1, 0),
        ("5章 分かれ目「5階」＝ 下りで階段が先 50%以上の いちばん上の階", float(max(D for D in DEST_LIST if pu_s[D]["p_down"] >= 0.5) == TOP_DOWN == 5), 1, 0),
        ("5章 グラフ「5階から下りる 52%」＝ normal.5.p_down（52.5%）の四捨五入・（50%以上）", float(SH["D5"] == 52 and PD[3] >= 0.5), 1, 0),
        ("5章「階段は、上りより下りのほうが速く歩ける」: 下りの割合は どの階でも 上りより高い", float(all(d > u for d, u in zip(PD, PU))), 1, 0),
    ]
    r5 = run(SEED_MAIN, 5, n=2000)                      # 5章「エレベーターは、上りでも下りでも、かかる時間はあまり変わりません」（モデルの run を呼ぶだけ。計算は変えない）
    ratio = float(np.median(r5["el_d"]) / np.median(r5["el_u"]))
    checks.append((f"5章「エレベーターは上りでも下りでも かかる時間はあまり変わらない」: 5階の真ん中の時間 下り÷上り ＝ {ratio:.2f}（0.85〜1.15）", ratio, 1.0, 0.15))
    for sc, tm, nm, first in ((SC0, TM0, "open3（冒頭）", "st"), (SC3, TM3, "look4_car1（3章）", "el"), (SC4, TM4, "rush6（4章）", "st")):
        checks += _sample_race_checks(sc, tm, nm, first)
    checks += [
        ("見本 4章（rush6）: かごは何度も止まる（乗る前のほかの止まりが2回以上）・ほかの人（灰色）を乗せている", float(len(SC4.pre) >= 2 and len(SC4.exits) >= 2), 1, 0),
        ("見本 4章（rush6）: 乗ったあとのほかの階の止まり・階段が先に着く（data.json）", float(SMP["rush6"]["stairs"] < SMP["rush6"]["el_t"]), 1, 0),
    ]
    # ---- 声の数字: 台本のどの文も、言う数字が SPOKEN（data.json・モデルの値から作った値）と1つ残らず一致する ----
    bad_lines, many = [], []
    for it in tl.items:
        if isinstance(it, lf.Line):
            got = sorted(_re.findall(NUM_RE, txt(it.id)))
            if got != sorted(SPOKEN.get(it.id, [])):
                bad_lines.append(f"{it.id}: {got} ≠ {sorted(SPOKEN.get(it.id, []))}")
            if len(got) > 1:
                many.append(it.id)
    for s_ in bad_lines:
        print("  声の数字が違う:", s_)
    checks.append((f"声の数字が data.json の値と一致（文ごと・{len(SPOKEN)}文）: 食い違い {len(bad_lines)}", float(not bad_lines), 1, 0))
    new_many = [i for i in many if i not in MANY_OK]
    checks.append((f"1文の声の数字は1つまで: 例外 {new_many}", float(not new_many), 1, 0))
    # ---- 時間割 ----
    ch = tl.chapters
    ends = [c[0] for c in ch[1:]] + [DUR]
    checks.append(("章は7つ・最初は0秒", float(len(ch) == 7 and ch[0][0] == 0), 1, 0))
    for (t0_, title), e_ in zip(ch, ends):
        checks.append((f"章「{title}」が10秒以上", float(e_ - t0_ >= 10), 1, 0))
    checks.append(("長さ 6分30秒〜10分30秒（台本の声が約5分半のため、仕様の「約8分」には届かない）", DUR, 510.0, 120.0))
    first40 = []
    for it in tl.items:
        if isinstance(it, lf.Line) and S(it.id) < 40:
            first40 += _re.findall(NUM_RE, txt(it.id))
    checks.append((f"冒頭40秒で声に出す数字は3つまで: {first40}", float(len(first40) <= 3), 1, 0))
    keys = box_keys()
    gaps_ = [b["t"] - a["t"] for a, b in zip(keys, keys[1:])]
    checks.append((f"数字の欄: 答えの数字は3秒以上見せる（変わるまでの最短 {min(gaps_):.1f}秒）", float(min(gaps_) >= 3.0), 1, 0))
    checks += [
        ("欄「60%」の赤丸は3秒以上", float(S("ch2") - (mid("c1_7", 0.6) + 0.3) >= 3), 1, 0),
        ("欄「3階」の赤丸は3秒以上", float(S("ch3") - (mid("c2_6", 0.6) + 0.3) >= 3), 1, 0),
        ("欄「27秒」の赤丸は3秒以上", float(S("c3_10") - (mid("c3_4", 0.7) + 0.3) >= 3), 1, 0),
        ("欄「51%」の赤丸は3秒以上", float(S("ch5") - (mid("c4_5", 0.6) + 0.3) >= 3), 1, 0),
        ("終了画面は まとめ の章の中", float(T_ES() > S("ch6") + 3), 1, 0),
        (f"区切りは約4秒（{EYE1() - EYE0():.1f}秒）", EYE1() - EYE0(), 4.0, 0.2),
        ("区切りは3章の終わりと4章の章カードの間", float(E("c3_10") <= EYE0() and EYE1() == S("ch4")), 1, 0),
        ("区切りは章ではない（chapters に入らない・章は7つのまま）", float(len(tl.chapters) == 7 and all(t0_ != EYE0() for t0_, _ in tl.chapters)), 1, 0),
        ("区切りは声なし（区切りの間に声の文がない）", float(not any(S(it.id) < EYE1() and E(it.id) > EYE0() for it in tl.items if isinstance(it, lf.Line))), 1, 0),
        (f"区切りの足あとと足音は {len(foot_times())} 回・すべて区切りの中", float(len(foot_times()) >= 10 and all(EYE0() <= tf <= EYE1() for _p, tf in foot_times())), 1, 0),
        ("区切りの文言 ＝ 左「分かれ目は、／3階」・右「朝の混雑なら？／下りなら？」",
         float(EYE_LEFT == ("分かれ目は、", "3階") and EYE_RIGHT == ("朝の混雑なら？", "下りなら？")), 1, 0),
        ("区切りの「3階」＝ 声の分かれ目（TOP_UP）と同じ値", float(f"{TOP_UP}階" == EYE_LEFT[1]), 1, 0),
        ("亀は左ページから右ページへ渡る（始め x<960・終わり x>960）", float(eye_x(EYE0()) < lf.GUTTER < eye_x(EYE1())), 1, 0),
        ("まとめの最後の説明の文（c6_6）は終了画面の前に言い終わる", float(E("c6_6") <= T_ES()), 1, 0),
        ("冒頭の早回しは無音の区間のうちに終わる", float(TM0.tv[-1] <= E("g0")), 1, 0),
        ("3章の早回しは無音の区間のうちに終わる", float(TM3.tv[-1] <= E("g3")), 1, 0),
        ("4章の早回しは無音の区間のうちに終わる", float(TM4.tv[-1] <= E("g4")), 1, 0),
        ("ふたりは「ふたりが同時に、1階を出発します」で現れ、早回しの前に並んでいる", float(S("c0_2") + 0.7 < TM0.tv[0]), 1, 0),
        ("冒頭のかごの動き（5階→1階→5階のイメージ）は、ふたりが出てくる前に5階へもどり終える・見本 open3 のかごは5階から始まる",
         float(OPEN_CAR_SEC <= S("c0_2") and open_car(OPEN_CAR_SEC - 1e-6)[0] > 4.999 and SC0.p["f0"] == 5 and abs(SC0.car_state(0.0)[0] - 5) < 1e-9), 1, 0),
        ("1章のマス目は無音の5秒のうちに埋まる", float(S("g1") + 0.2 + (dur("g1") - 0.6) <= E("g1")), 1, 0),
        ("2章のグラフは無音の区間のうちに描き終わる", float(S("g2") + 0.2 + (dur("g2") - 0.7) <= E("g2")), 1, 0),
    ]
    # ---- 字幕 ----
    worst_cps, worst_vis, worst_lines = 0.0, 1e9, 0
    for s_, e_, pause, ln, clip in tl._lines:
        vis = e_ - s_ + min(pause, lf.SUB_HOLD)
        worst_cps = max(worst_cps, len(clip.text) / vis)
        worst_vis = min(worst_vis, vis)
        worst_lines = max(worst_lines, len(lf.wrap_subtitle(clip.text)))
    checks += [
        (f"字幕: 1秒あたりの字数が12字以下（最大 {worst_cps:.1f}字）", float(worst_cps <= 12), 1, 0),
        (f"字幕: どの行も1秒以上出る（最短 {worst_vis:.1f}秒）", float(worst_vis >= 1.0), 1, 0),
        (f"字幕: 2行以内（最大 {worst_lines}行）", float(worst_lines <= 2), 1, 0),
    ]
    # ---- 画面の文字（0.25秒ごとに描いて調べる） ----
    if frames is not None:
        bad = overlaps(frames)
        for k, t in list(bad.items())[:12]:
            print(f"  重なり: {_ts(t)} 「{k[0]}」と「{k[1]}」")
        checks.append((f"文字どうしの重なりなし（0.5秒以上続くもの。章の付箋・1万回の合図は除く）: {len(bad)}組", float(len(bad) == 0), 1, 0))
        f0 = next(f for f in frames if f[0] == 0.5)
        names0 = {e[0] for e in f0[1]}
        checks.append(("0.5秒目までに 題字「階段とエレベーター」と右ページの問いが出ている（題字の赤い下線は 0〜0.3秒で引く）", float({"階段とエレベーター", "何階まで、", "階段が早い？"} <= names0), 1, 0))
        dig40 = sorted({e[0] for f in frames if f[0] < 40 for e in f[1] if any(c.isdigit() for c in e[0]) and not FURN.match(e[0])})
        checks.append((f"冒頭40秒に、画面に出る数字（を含む文字。階の名前と表示窓の数字は除く）は3つまで: {dig40}", float(len(dig40) <= 3), 1, 0))
        tes = T_ES() + 0.6
        out_es = [(f[0], e[0]) for f in frames if f[0] >= tes for e in f[1]
                  if e[1] < 40 or e[3] > 1880 or (e[1] < 980 and e[3] > 940) or e[4] > 936]
        for t, s_ in out_es[:5]:
            print(f"  終了画面でページの外・のどをまたぐ・字幕の帯に入る文字: {_ts(t)} 「{s_}」")
        checks.append((f"終了画面の文字はページの中（左 x 40〜940・右 x 980〜1880）・のどをまたがない・字幕の帯（y>936）に入らない: {len(out_es)}件",
                       float(not out_es), 1, 0))
        es_small = sorted({(e[0], round(e[5])) for f in frames if f[0] >= tes for e in f[1] if e[5] < 38})
        checks.append((f"終了画面の文字は すべて 38px 以上（付せんの答えは 64px・名前は 46px・問いかけは 68px・登録は 52px）: {es_small}", float(not es_small), 1, 0))
        es_last = [e for f in frames if f[0] >= T_ES() + 0.8 for e in f[1] if e[0] in END_SUB.split("\n")]
        checks.append(("終了画面の付せん「チャンネル登録」の3行（面白かったと思ってもらえたら／チャンネル登録・高評価／よろしくお願いします）が出る・52px 以上",
                       float(len(es_last) > 0 and min(e[5] for e in es_last) >= 51.5), 1, 0))
        small = {}
        for f in frames:
            for e in f[1]:
                if e[5] < 35.5:
                    small.setdefault((e[0], round(e[5])), f[0])
        for (s_, sz), t_ in list(small.items())[:12]:
            print(f"  36px未満の文字: {_ts(t_)} 「{s_}」 {sz}px")
        checks.append((f"画面の文字（字幕を除く）は すべて 36px 以上（幅480pxに縮めても読める。v5）: 36px未満 {len(small)}種", float(not small), 1, 0))
        br = [(f[0], e[0]) for f in frames for e in f[1] if e[3] > 1660 and e[4] > 930]
        for t, s_ in br[:5]:
            print(f"  右下に文字: {_ts(t)} 「{s_}」")
        checks.append((f"右下（x>1660・y>930）に文字を置かない: {len(br)}件", float(not br), 1, 0))
        k0 = box_keys()[0]["t"]
        in_box = lambda e: 1030 < e[1] and e[3] < 1800 and e[2] > 712
        box_units = ("%", "秒", "点", "階")
        miss = [f[0] for f in frames if k0 + 0.8 <= f[0] < T_ES() - 0.1 and not (EYE0() - 0.1 <= f[0] < EYE1() + 0.6)
                and not any(in_box(e) and e[0].endswith(box_units) for e in f[1])]
        checks.append((f"数字の欄は 最初の答えから終了画面まで出しっぱなし（区切りの4秒は除く。欠けたコマ {len(miss)}）", float(not miss), 1, 0))
        fe = [f for f in frames if EYE0() + 0.4 <= f[0] < EYE1() - 0.05]
        checks.append(("区切りの間は、数字の欄を出さない", float(bool(fe) and not any(in_box(e) and e[0].endswith(box_units) for f in fe for e in f[1])), 1, 0))
        checks.append(("区切りの間は、左「ここまで」＋2行・右「ここから」＋2行が出ている（0.5秒すぎから最後まで）",
                       float(all({"ここまで", "ここから", *EYE_LEFT, *EYE_RIGHT} <= {e[0] for e in f[1]} for f in fe if f[0] >= EYE0() + 0.5)), 1, 0))
        checks.append(("区切りの左右の文字はページの中（左は x<940・右は x>980）",
                       float(all((e[3] < 940 if e[0] in ("ここまで", *EYE_LEFT) else e[1] > 980) for f in fe for e in f[1]
                                 if e[0] in ("ここまで", "ここから", *EYE_LEFT, *EYE_RIGHT))), 1, 0))
        # 左ページの文字は x<945、右ページの文字は x>1030 に収まる（区切り・終了画面・章カードを除く）
        stray = [(f[0], e[0]) for f in frames for e in f[1]
                 if not (EYE0() <= f[0] < EYE1() + 0.4) and f[0] < T_ES() and e[0] not in OVERLAY_OK and (945 < e[3] and e[1] < 1030)]
        for t, s_ in stray[:5]:
            print(f"  のどにかかる文字: {_ts(t)} 「{s_}」")
        checks.append((f"見開きののど（x 945〜1030）に文字をまたがせない: {len(stray)}件", float(not stray), 1, 0))
        # 画面に出る数字は、data.json（の四捨五入）か閉じた式の値だけ
        allowed = set(range(0, 11)) | {10000, 24, 60, 120, 100, 50, 1.3}
        allowed |= {SH[k] for k in ("P3", "P3W", "GAP5", "S1_9", "P4", "P10", "R7", "D5", "CM24", "FL_LO", "FL_HI", "RUSH_BUSY", "RUSH_STOP")}
        allowed |= set(SH["SCEN"])
        for sc_ in (SC0, SC3, SC4):
            allowed |= {ihalf(sc_.T_st), ihalf(sc_.T_el)}
        for D in LOOK_ROWS:
            allowed |= set(look_row(D))
        shown_nums = {}
        for f in frames:
            for e in f[1]:
                if e[0] in OVERLAY_OK or e[0] in EYE_LEFT + EYE_RIGHT or e[0] in ("ここまで", "ここから"):
                    continue
                for m in _re.findall(r"\d+(?:\.\d+)?", e[0]):
                    shown_nums.setdefault(float(m), e[0])
        extra = sorted((v, s_) for v, s_ in shown_nums.items() if v not in allowed)
        for v, s_ in extra[:8]:
            print(f"  画面の数字 {v} が data.json の値でない: 「{s_}」")
        checks.append((f"画面に出る数字は、すべて data.json の値（の四捨五入）か閉じた式: 余分 {len(extra)}個", float(not extra), 1, 0))
        pcts = {int(m) for f in frames for e in f[1] for m in _re.findall(r"(\d+)%", e[0])}
        extra2 = sorted(pcts - PCT_OK)
        checks.append((f"画面に出る「N%」は、すべて data.json から作った値: 余分 {extra2}", float(not extra2), 1, 0))
        box_vals = {c[1] for kk in box_keys() for c in kk["cells"]}
        shown_box = {e[0] for f in frames for e in f[1] if in_box(e) and e[0].endswith(box_units)}
        extra3 = sorted(shown_box - box_vals)
        checks.append((f"数字の欄の数字は data.json の値だけ: 余分 {extra3}", float(not extra3), 1, 0))
        # 階の名前（建物の飾り）は 1〜建物の階数 の範囲だけ
        fl_max = max(SC0.n, SC3.n, SC4.n, 10)
        bad_fl = sorted({e[0] for f in frames for e in f[1] if _re.fullmatch(r"\d+階", e[0]) and not (1 <= int(e[0][:-1]) <= fl_max)})
        checks.append((f"階の名前は 1〜{fl_max}階 の範囲: {bad_fl}", float(not bad_fl), 1, 0))
        # 実在の人・会社・建物の名前・コードの話を出さない
        bad_words = ("三菱", "日立", "東芝", "オーチス", "シンドラー", "フジテック", "JIS", "建築基準法", "告示", "ロンキ", "Ronchi", "Powell", "np.", "seed")
        all_txt = " ".join(e[0] for f in frames for e in f[1]) + " ".join(tl.clip(it.id).text for it in tl.items if isinstance(it, lf.Line))
        hit_w = [w for w in bad_words if w in all_txt]
        checks.append((f"実在の会社名・出典・コードの話を画面と声に出さない: {hit_w}", float(not hit_w), 1, 0))
        # 早回しのコマに、人が描かれている（階段の人・エレベーターの人）
        race_frames = [f for f in frames if TM0.tv[0] + 0.5 <= f[0] < TM0.tv[-1] or TM3.tv[0] + 0.5 <= f[0] < TM3.tv[-1] or TM4.tv[0] + 0.5 <= f[0] < TM4.tv[-1]]
        checks.append((f"早回しのコマ（{len(race_frames)}コマ）には、2人以上の人が描かれている", float(all(f[2] >= 2 for f in race_frames)), 1, 0))
    flat = [(n_, float(v), float(e), tol) for n_, v, e, tol in checks]
    check_answers(flat)
    print(f"場面の照合 {len(flat)} 件 OK")
    return len(flat)


# ============================================================
# 書き出し
# ============================================================
def scene_main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"台本の長さ: {DUR:.1f}秒（{lf._mmss(DUR)}）{'  ※ --fake-voice の見積もり' if FAKE else ''}")
    for t0_, title in tl.chapters:
        print(f"  {lf._mmss(t0_)} {title}")
    args = sys.argv[1:]
    if "--readings" in args:
        write_readings(OUT / "readings.log")
        return
    if "--wraps" in args:
        for it in tl.items:
            if isinstance(it, lf.Line):
                print(f"{it.id}: {' ／ '.join(lf.wrap_subtitle(tl.clip(it.id).text))}")
        return
    if "--scenecheck" in args:
        frames = scan()
        scene_checks(frames)
        return
    if "--stills" in args:
        if "--at" in args:
            for tt in [float(x) for x in args[args.index("--at") + 1].split(",")]:
                lf.still(draw, tt, OUT / "work_v3" / f"at_{tt:06.1f}.png")
        else:
            stills_keep(draw, still_times(), OUT / "work_v3" / "stills")
        return
    if "--preview" in args:
        lf.render(draw, DUR, OUT / f"{SLUG}.preview.mp4", build_audio(), timeline=tl, preview=True)
        return
    if FAKE:
        raise SystemExit("--fake-voice は確認用です。本番は AivisSpeech を起動してから")
    frames = scan()
    scene_checks(frames)
    write_screen_text(OUT / "screen_text.txt", frames)
    lf.render(draw, DUR, OUT / f"{SLUG}.mp4", build_audio(), timeline=tl)
    write_transcript(OUT / "transcript.long.txt")
    write_readings(OUT / "readings.log")
    stills_keep(draw, still_times(), OUT / "stills_v3_final")
    lf.still(draw, EYE0() + 2.0, OUT / "eyecatch_final.png")
    print("区切り:", OUT / "eyecatch_final.png", f"（{_ts(EYE0())}〜{_ts(EYE1())}）")
    print("完成:", OUT / f"{SLUG}.mp4")


if __name__ == "__main__":
    scene_main()
