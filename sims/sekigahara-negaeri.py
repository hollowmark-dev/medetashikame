"""関ヶ原の戦い、寝返りがなければどちらが勝つ？ 1万回の合戦。— 2026-10-31 作成（公開予定 11.15・ナレーションなし・45秒前後）

くらべるのは「寝返りなし（寝返った隊は西軍のまま戦う）で1万回やったときの、西軍が勝った回の割合 p と 東軍が勝った回の割合 q」。
事実確認は research/2026-10-31_sekigahara_FACTCHECK.md。兵の数・布陣・時刻は説が割れるので、割れる所は幅で回した。

【計算の前に固定した置き方】（この下の数字は 1万回を回す前に決めた。結果を見て変えていない。感度は --model で別に出す）
  隊      : 西軍9隊・東軍8隊。兵の数は 隊ごとに 出典の幅（下の UNITS）から 一様にでたらめ。
            西軍 = 石田 / 島津 / 小西 / 宇喜多 / 大谷（戦う5隊）、小早川 / 脇坂ら4隊（寝返った隊）、毛利・吉川 / 長宗我部ら（南宮山で動かなかった隊）
            東軍 = 福島 / 黒田・細川 / 加藤ら / 井伊ら / 藤堂ら / 寺沢ら / 家康本隊（後から来る予備）、池田ら（南宮山の毛利勢に備えた隊）
            徳川秀忠の別働隊（上田方面）は戦場にいなかったので入れない。
  戦線    : 北（笹尾山の石田・島津 対 黒田・細川・加藤ら）／中（天満山の宇喜多・小西 対 福島・井伊ら）／南（山中の大谷・小早川 対 藤堂ら・寺沢ら）／東（南宮山 毛利ら 対 池田ら）。
            片方の隊が戦線で全部いなくなったら、その戦線の相手側の隊は 1時間かけて となりの戦線へ移る。家康本隊は 来たあと、いちばん東軍が押されている戦線に入る。
  強さ    : 1人あたりの強さは 東西同じ。1時間に 敵1人を倒す割合 β（0.10〜0.25 から一様）。ランチェスターの2次法則（戦線ごとに 東西の力の積み上げ × β が 相手の兵を減らす）。
            1戦線・15分ごとに 運（対数正規・ばらつき 0.25）。山の上（笹尾山・天満山・松尾山・南宮山）にいる隊は 倒す力が H 倍（H は 1.0〜1.5 から一様）。
  士気    : 隊のうち 実際に戦う割合 f。ふつうの隊は 0.6〜1.0。史料で「様子見・なかなか動かなかった」と伝わる隊（島津・小早川・脇坂ら・毛利・長宗我部ら）は 0.3〜1.0。
            残りは 様子見で戦わない（減りもしない）。隊の戦力（戦う兵）が 25〜50%（一様）減ったら その隊は崩れて戦場を去る（残りは「失った」に数える）。
  動く時刻: 戦いの始まり t0 は 朝8時〜10時から一様（8時説と10時説の両方をカバー）。隊が加わる時刻は t0 から 先鋒 0〜1時間 / 後続（島津・加藤ら・寺沢ら・寝返りの隊）0.5〜2.5時間 /
            家康本隊 2〜5時間 / 動かなかった隊（2026-10-31 の差し替え後は 戦わせる条件を使わない）1〜4時間 後。
  決着    : 夕方（17時）まで。参戦した兵のうち 失った割合（死傷・隊の崩れ）が 先に 50% に達した側が負け。1時間経つまでは判定しない。17時までにどちらも50%未満なら「決着なし」。
  条件    : ①史実どおり  = 小早川と脇坂ら4隊は 寝返る時刻まで戦わず、そのあと東軍として大谷隊側から戦う。寝返る時刻 = 40%は開戦と同時（白峰・渡邊説）、60%は 11時〜13時（従来の正午ごろ説）。
                            南宮山の隊は動かない（東軍の池田ら も 動かず備えるだけ）。
            ②寝返りなし  = 小早川と脇坂ら4隊が 西軍のまま 戦う。南宮山の隊は動かない。  ← 答えを決める条件
            ④様子見のまま（画面では ③と呼ぶ）= 小早川と脇坂ら4隊は 寝返らず、西軍としても戦わず 動かない（様子見のまま）。南宮山の隊も動かない。
            ①②④は 同じ乱数（兵の数・戦う割合・時刻・運）を使う（条件のちがいだけが結果をかえる）。
            （2026-10-31 まで使っていた「寝返りも不動もなし」は 画面から外した。--model では 条件3として残る）
  小早川の兵の数: 70% は 15,000〜15,700（15,600 とする資料が多い）、30% は 5,000〜10,000（松尾山に上がったのは数千とする見方）。
  置かないもの: 兵の腕前・武器・指揮官・天気・霧・補給・戦線の幅の限り（強さは東西同じ）。島津の「敵中突破」は決着のあとのことなので 入れない。「問鉄砲」は 創作説なので 使わない。

【答えの決め方】（answer_by_rule。計算の前に固定。台本のまま）
  条件②の 1万回で、西軍が勝った割合 p・東軍が勝った割合 q とする。
  p ≥ 60% → 西軍が勝つ ／ q ≥ 60% → 東軍が勝つ ／ それ以外（決着なしを含む）→ ほぼ互角
  同じ画面に ①の p・④の p も出す（置き方で答えが逆になることを見せる）。

【あわせて出す数字】（1万回のばらつき）
  ・西軍が勝つのは 何回に1回／東軍が勝つのは 何回に1回／決着なしは 何回に1回
  ・損失の差 d = 西軍の損失率 − 東軍の損失率（17時または決着まで）。中央値（1万回の ちょうど真ん中の値）、いちばん西軍に良かった回／いちばん悪かった回
  ・ひねり: 条件①②④の p（④＝様子見のまま。2,500回の感度ではなく、同じ乱数の1万回で回し直した数字）

【絵について】計算は 17隊のまま。旗の大きさは 残っている兵の数の平方根に比例（兵が減ると旗が小さくなる）。見本の1回は 条件②の1万回の中の1回そのもの。

問い: 「寝返った隊が / 西軍のまま戦っていたら、/ どちらが勝つ？」（2026-10-31 統括の判断で変更）
      選択肢: 西軍が勝つ ／ ほぼ互角 ／ 東軍が勝つ（正解の記号は A か C（B 以外）。西→互角→東の並びのまま、結果の位置で決まる）
見せ方: 見本の1回（朝→夕の合戦）→ 損失の差を1万回ぶん積む →「西軍○回・東軍○回・決着なし○回」→ 答え → ひねり（①史実どおり・②西軍のまま戦う・③様子見のまま。置き方で答えが逆になる）
締め: 「勝ち負けを分けたのは、寝返った隊が戦ったかどうか」＋「あなたなら、どちらの陣に立ちますか？」
言葉: 「中央値」は初出で「1万回の ちょうど真ん中の値」と添える。見本は「たとえば、この1回では」。画面に「史実の数字は諸説あり・計算での見立て」を小さく1回。

【2026-10-31 統括の判断による変更】（1万回の②の結果は変えていない）
  1. 問い3行を「寝返った隊が／西軍のまま戦っていたら、／どちらが勝つ？」に。上の問い2行も同じ文言。
  2. ひねりを「では、寝返らずに様子見のままだったら？」に差し替え。条件④（小早川・脇坂らが動かない）を ①②と同じ乱数の1万回で回した数字を出す。
     ①史実どおり・②西軍のまま戦う・③様子見のまま（内部名 条件4）の3本の棒。置き方で答えが逆になることを隠さず見せる。「動かなかった軍も戦っていたら」は外した。
  3. 締めを「勝ち負けを分けたのは、寝返った隊が戦ったかどうか」＋視聴者への問いに。
"""
import hashlib
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SLUG = "sekigahara-negaeri"
OUT = Path(__file__).resolve().parents[1] / "out" / SLUG

# ---- MODEL BEGIN ----
N_TRIAL = 10000
SEED_MAIN = 20261115
DT = 0.25                                            # 時間の刻み（時間）
K_STEPS = 40                                         # 最大 10時間
T_END = 17.0                                         # 夕方（時）
T_MIN_JUDGE = 1.0                                    # 判定を始める（開戦から）
TRAVEL = 1.0                                         # 戦線を移るのにかかる時間
LOSE_LINE = 0.5                                      # 失った割合がこれに達した側が負け
P_STRONG = 0.60                                      # 答えのしきい値

F_OK, F_RL = (0.6, 1.0), (0.3, 1.0)                  # 戦う割合（ふつう／様子見の傾向）
A1, A2, A_RES, A_ST = (0.0, 1.0), (0.5, 2.5), (2.0, 5.0), (1.0, 4.0)
FR_N, FR_C, FR_S, FR_X = 0, 1, 2, 3
ADJ = {0: (1,), 1: (0, 2, 3), 2: (1,), 3: (1,)}
FRONT_NAME = ["北（笹尾山）", "中（天満山）", "南（山中）", "東（南宮山）"]

# key, 札, 側(0=西 1=東), 戦線, 山の上, 兵の数の幅, 戦う割合の幅, 加わる時刻の幅, 区分(w=ふつう d=寝返りの隊 s=動かなかった隊 r=予備)
UNITS = [
    ("ISHI", "石田", 0, FR_N, 1, (4000, 6000), F_OK, A1, "w"),
    ("SHIM", "島津", 0, FR_N, 0, (1000, 1700), F_RL, A2, "w"),
    ("KONI", "小西", 0, FR_C, 0, (4000, 6000), F_OK, A1, "w"),
    ("UKIT", "宇喜多", 0, FR_C, 1, (10000, 17220), F_OK, A1, "w"),
    ("OTAN", "大谷", 0, FR_S, 0, (4500, 6500), F_OK, A1, "w"),
    ("KOBA", "小早川", 0, FR_S, 1, (15000, 15700), F_RL, A2, "d"),      # 兵の数は draw で混合
    ("FOUR", "脇坂ら", 0, FR_S, 0, (3400, 4290), F_RL, A2, "d"),
    ("MORI", "毛利・吉川", 0, FR_X, 1, (15000, 18000), F_RL, A_ST, "s"),
    ("CHOS", "長宗我部ら", 0, FR_X, 0, (6000, 9960), F_RL, A_ST, "s"),
    ("FUKU", "福島", 1, FR_C, 0, (5500, 6500), F_OK, A1, "w"),
    ("KURO", "黒田・細川", 1, FR_N, 0, (9000, 10500), F_OK, A1, "w"),
    ("KATO", "加藤ら", 1, FR_N, 0, (8500, 10700), F_OK, A2, "w"),
    ("II", "井伊ら", 1, FR_C, 0, (6000, 7100), F_OK, A1, "w"),
    ("TODO", "藤堂ら", 1, FR_S, 0, (4500, 5500), F_OK, A1, "w"),
    ("TERA", "寺沢ら", 1, FR_S, 0, (4000, 5200), F_OK, A2, "w"),
    ("IEYA", "家康", 1, -1, 0, (20000, 30000), F_OK, A_RES, "r"),
    ("IKED", "池田ら", 1, FR_X, 0, (12760, 14000), F_OK, A_ST, "s"),
]
U = len(UNITS)
KEYS = [u[0] for u in UNITS]
IX = {k: i for i, k in enumerate(KEYS)}
SIDE0 = np.array([u[2] for u in UNITS], np.int8)
FRONT0 = np.array([u[3] for u in UNITS], np.int8)
HI = np.array([u[4] for u in UNITS], bool)
N_LO = np.array([u[5][0] for u in UNITS], float)
N_HI = np.array([u[5][1] for u in UNITS], float)
F_LO = np.array([u[6][0] for u in UNITS], float)
F_HI = np.array([u[6][1] for u in UNITS], float)
A_LO = np.array([u[7][0] for u in UNITS], float)
A_HI = np.array([u[7][1] for u in UNITS], float)
GRP = [u[8] for u in UNITS]
DEF = [IX["KOBA"], IX["FOUR"]]
STATIC = [i for i, g in enumerate(GRP) if g == "s"]
IE = IX["IEYA"]
KOBA = IX["KOBA"]

COND_NAME = {1: "①史実どおり", 2: "②西軍のまま戦う", 3: "（寝返りも不動もなし・画面では使わない）", 4: "③様子見のまま（小早川・脇坂らは動かない）"}
CONDS = (1, 2, 4)                                    # 1万回で回す条件（画面で使う）
CFG0 = dict(beta=(0.10, 0.25), hi=(1.0, 1.5), noise=0.25, koba_idle=False, ieya_scale=1.0, rout=(0.25, 0.50),
            static_f=None, lose=LOSE_LINE)


def answer_by_rule(p, q):
    """p: 西軍が勝った割合、q: 東軍が勝った割合（条件② の1万回）。戻り値 'west'（西軍が勝つ）/'even'（ほぼ互角）/'east'（東軍が勝つ）"""
    if p >= P_STRONG:
        return "west"
    if q >= P_STRONG:
        return "east"
    return "even"


def draw_trial(seed, h):
    """1回ぶんの乱数（兵の数・戦う割合・時刻・運）。①②④と見本で同じものを使う"""
    rng = np.random.default_rng([seed, h])
    uni = rng.random((U, 4))
    sc = rng.random(8)
    nz = rng.standard_normal((K_STEPS, 4))
    return uni, sc, nz


def stack_trials(seed, n):
    UN = np.zeros((n, U, 4))
    SC = np.zeros((n, 8))
    NZ = np.zeros((n, K_STEPS, 4))
    for h in range(n):
        UN[h], SC[h], NZ[h] = draw_trial(seed, h)
    return UN, SC, NZ


def derive(UN, SC, NZ, cfg=CFG0):
    """乱数 → 兵の数・戦う割合・加わる時刻・崩れる線・β・H・始まりの時刻・寝返る時刻"""
    n = len(SC)
    N = N_LO + UN[:, :, 0] * (N_HI - N_LO)
    big = SC[:, 3] < 0.7                                              # 小早川: 70% は 通説の数、30% は 少なく見る説
    N[:, KOBA] = np.where(big, 15000 + 700 * UN[:, KOBA, 0], 5000 + 5000 * UN[:, KOBA, 0])
    N[:, IE] *= cfg["ieya_scale"]
    f_lo, f_hi = F_LO.copy(), F_HI.copy()
    if cfg["static_f"] is not None:
        for i in STATIC:
            f_lo[i], f_hi[i] = cfg["static_f"]
    f = f_lo + UN[:, :, 1] * (f_hi - f_lo)
    arr = A_LO + UN[:, :, 2] * (A_HI - A_LO)
    r = cfg["rout"][0] + UN[:, :, 3] * (cfg["rout"][1] - cfg["rout"][0])
    beta = cfg["beta"][0] + SC[:, 0] * (cfg["beta"][1] - cfg["beta"][0])
    H = cfg["hi"][0] + SC[:, 1] * (cfg["hi"][1] - cfg["hi"][0])
    t0 = 8.0 + 2.0 * SC[:, 2]
    tdef_abs = np.where(SC[:, 4] < 0.4, t0, 11.0 + 2.0 * SC[:, 5])
    tdef = np.maximum(0.0, tdef_abs - t0)
    nz = np.exp(cfg["noise"] * NZ - 0.5 * cfg["noise"] ** 2)
    return dict(N=N, f=f, arr=arr, r=r, beta=beta, H=H, t0=t0, tdef=tdef, nz=nz)


def participation(cond, cfg=CFG0):
    part = np.ones(U, bool)
    if cond in (1, 2, 4):
        part[STATIC] = False
    if cond == 4 or (cfg["koba_idle"] and cond in (2,)):
        part[DEF] = False
    return part


def simulate(D, cond, cfg=CFG0, rec=False):
    """条件 cond（1〜3）で 全部の回を 同時に回す。戻り値: dict（win 0=西 1=東 2=決着なし, 損失率, 決着の時刻 など）"""
    n = len(D["t0"])
    N, f, arr, r = D["N"], D["f"], D["arr"], D["r"]
    S0 = N * f
    S = S0.copy()
    side = np.tile(SIDE0, (n, 1))
    front = np.tile(FRONT0, (n, 1))
    part = np.tile(participation(cond, cfg), (n, 1))
    act_from = np.where(part, arr, np.inf)
    if cond == 1:
        side[:, DEF] = 1
        act_from[:, DEF] = np.maximum(arr[:, DEF], D["tdef"][:, None])
    base_arr = act_from.copy()
    routed = np.zeros((n, U), bool)
    hm = np.where(HI[None, :], D["H"][:, None], 1.0)
    done = np.zeros(n, bool)
    win = np.full(n, 2, np.int8)
    loss_w = np.zeros(n)
    loss_e = np.zeros(n)
    t_dec = np.zeros(n)
    ar = np.arange(n)
    trace = [] if rec else None

    def sums(mask, w):
        out = np.zeros((n, 2, 4))
        for u in range(U):
            idx = np.nonzero(mask[:, u] & (front[:, u] >= 0))[0]
            if len(idx):
                out[idx, side[idx, u], front[idx, u]] += w[idx, u]
        return out

    for k in range(K_STEPS):
        tau = k * DT
        clock = D["t0"] + tau
        alive = part & ~routed & (S > 0)
        active = alive & (tau >= act_from) & ~done[:, None]
        # 家康本隊は 加わった瞬間に いちばん東軍が押されている戦線へ
        need = np.nonzero(active[:, IE] & (front[:, IE] < 0))[0]
        if len(need):
            P0 = sums(active, S * hm)
            ratio = np.where(P0[:, 0, :3] > 0, (P0[:, 1, :3] + 1.0) / (P0[:, 0, :3] + 1.0), np.inf)
            pick = np.argmin(ratio, axis=1)
            pick = np.where(np.isfinite(ratio.min(axis=1)), pick, FR_C)
            front[need, IE] = pick[need]
        Pw = sums(active, S * hm)
        Ss = sums(active, S)
        nzk = D["nz"][:, k, :]
        dm = (D["beta"] * DT)[:, None, None] * nzk[:, None, :] * Pw[:, ::-1, :]
        frac = np.minimum(1.0, dm / np.maximum(Ss, 1e-9))
        ev = []
        for u in range(U):
            idx = np.nonzero(active[:, u] & (front[:, u] >= 0))[0]
            if len(idx):
                S[idx, u] *= 1.0 - frac[idx, side[idx, u], front[idx, u]]
        ro = active & (S > 0) & ((S0 - S) >= r * S0)
        if ro.any():
            S[ro] = 0.0
            routed |= ro
            if rec:
                ev = [(u, int(front[0, u])) for u in range(U) if ro[0, u]]
        # 戦線の相手がいなくなったら となりの戦線へ
        alive2 = part & ~routed & (S > 0)
        Sp = sums(alive2, S)
        act2 = alive2 & (tau >= act_from) & ~done[:, None]
        for u in range(U):
            idx = np.nonzero(act2[:, u] & (front[:, u] >= 0))[0]
            if not len(idx):
                continue
            cleared = Sp[idx, 1 - side[idx, u], front[idx, u]] <= 0
            idx = idx[cleared]
            for ff in range(4):
                sel = idx[front[idx, u] == ff]
                if not len(sel):
                    continue
                best = np.full(len(sel), -1)
                bv = np.zeros(len(sel))
                for g in ADJ[ff]:
                    v = Sp[sel, 1 - side[sel, u], g]
                    better = v > bv
                    best = np.where(better, g, best)
                    bv = np.where(better, v, bv)
                mv = best >= 0
                front[sel[mv], u] = best[mv]
                act_from[sel[mv], u] = tau + DT + TRAVEL
        # 失った割合
        arrived = part & (tau >= base_arr)
        base = np.zeros((n, 2))
        lost = np.zeros((n, 2))
        for s_ in (0, 1):
            m = arrived & (side == s_)
            base[:, s_] = (S0 * m).sum(1)
            lost[:, s_] = ((S0 - S) * m).sum(1)
        fr = lost / np.maximum(base, 1.0)
        cand = ~done & (tau >= T_MIN_JUDGE)
        lose = cand & ((fr[:, 0] >= cfg["lose"]) | (fr[:, 1] >= cfg["lose"]))
        winner = np.where(fr[:, 0] >= fr[:, 1], 1, 0)
        endnow = ~done & ~lose & (clock + DT > T_END)
        fin = lose | endnow
        win[lose] = winner[lose]
        win[endnow] = 2
        loss_w[fin], loss_e[fin] = fr[fin, 0], fr[fin, 1]
        t_dec[fin] = tau
        if rec:
            trace.append(dict(k=k, tau=tau, clock=float(clock[0]), S=S[0].copy(), front=front[0].copy(), side=side[0].copy(),
                              active=active[0].copy(), routed=routed[0].copy(), part=part[0].copy(), arrived=arrived[0].copy(),
                              fr=fr[0].copy(), rout=ev, done=bool(done[0] | fin[0])))
        done |= fin
        if done.all():
            break
    out = dict(win=win, loss_w=loss_w, loss_e=loss_e, t_dec=t_dec, t0=D["t0"], d=loss_w - loss_e)
    if rec:
        out["trace"] = trace
        out["S0"] = S0[0].copy()
    return out


def stats(res):
    n = len(res["win"])
    w = res["win"]
    d = res["d"]
    return dict(p=float((w == 0).mean()), q=float((w == 1).mean()), z=float((w == 2).mean()), n=n,
                nw=int((w == 0).sum()), ne=int((w == 1).sum()), nz=int((w == 2).sum()),
                med_lw=float(np.median(res["loss_w"])), med_le=float(np.median(res["loss_e"])), med_d=float(np.median(d)),
                best=int(np.argmin(d)), worst=int(np.argmax(d)), t_med=float(np.median(res["t_dec"])))


def pct(x):
    return int(math.floor(x * 100 + 0.5))


def _model_hash():
    src = Path(__file__).read_text(encoding="utf-8")
    a = src.index("# ---- MODEL BEGIN ----")
    b = src.index("# ---- MODEL END ----")
    return hashlib.md5(src[a:b].encode("utf-8")).hexdigest()[:10]


_RES = {}


def results():
    """1万回 × 3条件。out/<slug>/cache/ に置く"""
    if _RES:
        return _RES["m"]
    from engine.parts import cache_dir
    f = cache_dir(SLUG) / f"battles_{_model_hash()}.npz"
    UN, SC, NZ = stack_trials(SEED_MAIN, N_TRIAL)
    D = derive(UN, SC, NZ)
    if f.exists():
        z = np.load(f)
        res = {c: {k: z[f"{c}_{k}"] for k in ("win", "loss_w", "loss_e", "t_dec", "t0", "d")} for c in CONDS}
    else:
        import time
        t0 = time.time()
        res = {c: simulate(D, c) for c in CONDS}
        print(f"  1万回の合戦 ×3条件 {time.time() - t0:.0f}秒")
        np.savez_compressed(f, **{f"{c}_{k}": v for c in res for k, v in res[c].items() if k in ("win", "loss_w", "loss_e", "t_dec", "t0", "d")})
    st = {c: stats(res[c]) for c in res}
    _RES["m"] = dict(res=res, st=st, D=D, UN=UN, SC=SC, NZ=NZ, key=answer_by_rule(st[2]["p"], st[2]["q"]))
    return _RES["m"]


SENS = (("基準", {}),
        ("β を小さく 0.05〜0.15", dict(beta=(0.05, 0.15))),
        ("β を大きく 0.20〜0.40", dict(beta=(0.20, 0.40))),
        ("山の上の利なし H=1", dict(hi=(1.0, 1.0))),
        ("山の上の利 強い 1.3〜2.0", dict(hi=(1.3, 2.0))),
        ("崩れる線 0.4〜0.7", dict(rout=(0.4, 0.7))),
        ("崩れる線 0.15〜0.3", dict(rout=(0.15, 0.3))),
        ("家康本隊の数 ×0.5", dict(ieya_scale=0.5)),
        ("家康本隊の数 ×1.3", dict(ieya_scale=1.3)),
        ("運のばらつき 0.5", dict(noise=0.5)),
        ("負けの線 40%", dict(lose=0.4)),
        ("負けの線 60%", dict(lose=0.6)))


def sensitivity(n=2500):
    """置き方を変えたとき 答えが動くか（情報）"""
    UN, SC, NZ = stack_trials(SEED_MAIN + 7, n)
    rows = []
    for nm, kw in SENS:
        cfg = dict(CFG0)
        cfg.update(kw)
        D = derive(UN, SC, NZ, cfg)
        r = [stats(simulate(D, c, cfg)) for c in CONDS]
        rows.append((nm, r))
    return rows


def report():
    r = results()
    st = r["st"]
    print(f"乱数の種 {SEED_MAIN}  {N_TRIAL}回  隊 {U}（西{int((SIDE0 == 0).sum())}・東{int((SIDE0 == 1).sum())}）")
    for c in CONDS:
        s = st[c]
        print(f"  {COND_NAME[c]}: 西軍が勝った {s['p'] * 100:.1f}%（{s['nw']}回）  東軍が勝った {s['q'] * 100:.1f}%（{s['ne']}回）  決着なし {s['z'] * 100:.1f}%（{s['nz']}回）"
              f"  損失率の中央値 西{s['med_lw'] * 100:.0f}% 東{s['med_le'] * 100:.0f}%  決着までの中央値 {s['t_med']:.1f}時間")
    s = st[2]
    print(f"  答え（条件②）: p={s['p'] * 100:.2f}% q={s['q'] * 100:.2f}% → {r['key']}")
    d = r["res"][2]["d"]
    print(f"  損失の差 d（西−東）: 最小 {d.min() * 100:.0f}pt（いちばん西軍に良い回 #{s['best']}）  最大 {d.max() * 100:.0f}pt（いちばん悪い回 #{s['worst']}）  中央値 {s['med_d'] * 100:.1f}pt")
    for nm, i in (("最良", s["best"]), ("最悪", s["worst"])):
        rs = r["res"][2]
        print(f"    {nm}の回 #{i}: 西軍の損失 {rs['loss_w'][i] * 100:.0f}%  東軍の損失 {rs['loss_e'][i] * 100:.0f}%  勝ち {['西', '東', 'なし'][int(rs['win'][i])]}")
    print(f"  何回に1回: 西軍勝ち 約{1 / max(s['p'], 1e-9):.1f}回  東軍勝ち 約{1 / max(s['q'], 1e-9):.1f}回  決着なし 約{1 / max(s['z'], 1e-9):.1f}回")
    D = r["D"]
    tot_w = ((D["N"] * (SIDE0 == 0)).sum(1))
    tot_e = ((D["N"] * (SIDE0 == 1)).sum(1))
    print(f"  兵の数の合計（全員そろえた場合・戦う割合をかける前）: 西軍 中央値 {int(np.median(tot_w)):,}人  東軍 中央値 {int(np.median(tot_e)):,}人")
    S0 = D["N"] * D["f"]
    for c in (2,):
        part = participation(c)
        sw = (S0 * (part & (SIDE0 == 0))).sum(1)
        se = (S0 * (part & (SIDE0 == 1))).sum(1)
        print(f"  条件②で戦う兵（戦う割合ぶん）: 西軍 中央値 {int(np.median(sw)):,}人  東軍 中央値 {int(np.median(se)):,}人（家康本隊 {int(np.median(S0[:, IE])):,}人をふくむ）")


def report_sensitivity():
    print("感度（置き方を変える。各2500回・情報）: 西軍が勝つ%／東軍が勝つ%／決着なし%")
    for nm, rs in sensitivity():
        cells = "   ".join(f"{COND_NAME[c_][0]}{s['p'] * 100:4.0f}/{s['q'] * 100:4.0f}/{s['z'] * 100:4.0f}" for c_, s in zip(CONDS, rs))
        print(f"  {nm}: {cells}  → ②は {answer_by_rule(rs[1]['p'], rs[1]['q'])}")


# ---- MODEL END ----


if __name__ == "__main__" and "--model" in sys.argv:
    OUT.mkdir(parents=True, exist_ok=True)
    if "--timing" in sys.argv:
        import time
        t0_ = time.time()
        UN_, SC_, NZ_ = stack_trials(SEED_MAIN, 1000)
        t1_ = time.time()
        simulate(derive(UN_, SC_, NZ_), 2)
        print(f"1000回の乱数 {t1_ - t0_:.1f}秒  合戦 {time.time() - t1_:.1f}秒")
        sys.exit(0)
    report()
    if "--nosens" not in sys.argv:
        report_sensitivity()
    sys.exit(0)


# =====================================================================
# 見本（絵に出す1回の合戦）を、1万回の中から選ぶ
# =====================================================================
_SAMPLE = {}


def samples():
    """条件②の1万回のうち、答えの側が勝った回（互角なら決着がついた回）で、損失の差 d が その中央値にいちばん近い1回。
    1万回の中の1回そのもの（同じ乱数で動きを記録し直す）"""
    if _SAMPLE:
        return _SAMPLE
    r = results()
    res = r["res"][2]
    win, key = res["win"], r["key"]
    if key == "west":
        cand = np.nonzero(win == 0)[0]
    elif key == "east":
        cand = np.nonzero(win == 1)[0]
    else:
        cand = np.nonzero(win != 2)[0]
    dd = res["d"][cand]
    h = int(cand[np.argmin(np.abs(dd - np.median(dd)))])
    D1 = derive(r["UN"][h:h + 1], r["SC"][h:h + 1], r["NZ"][h:h + 1])
    rec = simulate(D1, 2, rec=True)
    _SAMPLE.update(h=h, rec=rec, D1=D1, n_cand=len(cand))
    return _SAMPLE


if __name__ == "__main__" and "--pick" in sys.argv:
    S = samples()
    rec = S["rec"]
    print(f"見本: 回 #{S['h']}（候補 {S['n_cand']}回）  勝ち {['西', '東', 'なし'][int(rec['win'][0])]}  西軍の損失 {rec['loss_w'][0] * 100:.0f}%  東軍の損失 {rec['loss_e'][0] * 100:.0f}%  決着まで {rec['t_dec'][0]:.2f}時間  始まり {rec['t0'][0]:.2f}時")
    print("  兵（戦う分）:", {KEYS[i]: int(rec['S0'][i]) for i in range(U)})
    for tr in rec["trace"]:
        ev = [KEYS[u] for u, _ in tr["rout"]]
        fl = "".join(str(int(x)) for x in tr["front"])
        print(f"  k={tr['k']:2d} 午前{tr['clock']:.2f} 西{tr['fr'][0] * 100:3.0f}% 東{tr['fr'][1] * 100:3.0f}%  崩れ={ev}  戦線={fl}")
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
note.DATE = "11.15"                                  # 日付欄（公開予定日）

C_WEST, C_EAST, C_DEF = "#c9423c", "#2f6cb3", "#8c4fb0"
C_WEST_D, C_EAST_D, C_DEF_D = "#7e231f", "#173f73", "#55286f"
C_WEST_L, C_EAST_L = "#dfaaa4", "#a9c0dc"           # 動かなかった隊（うすい色）
C_NONE = "#8d8d96"

# 記号の並び・正解は ここ（と comment.txt）だけ。2026-10-31 統括の指示: 正解の記号は B 以外（11/14 が B のため）。
# 結果が「西軍が勝つ」だったので、自然な並び 西軍→互角→東軍 のまま、正解は A（1番目）。
LABELS = ["西軍が勝つ", "ほぼ互角", "東軍が勝つ"]
KEY_LABEL = {"west": "西軍が勝つ", "even": "ほぼ互角", "east": "東軍が勝つ"}
CORRECT = 0                                         # answer_by_rule の結果の位置（A）

BIG_Q3 = ["寝返った隊が", "西軍のまま戦っていたら、", "どちらが勝つ？"]              # 1コマ目の3行（同じ大きさ）
BIG_Q = ["寝返った隊が西軍のまま戦っていたら、", "どちらが勝つ？"]                    # 定位置（上）の2行
DETAIL_RULE = "関ヶ原の戦い。史実では東軍の勝ち"
DETAIL = "史実の数字は諸説あり。計算での見立て（強さは東西同じ）"

# ---------- 時間割（動画の秒） ----------
T_CHO = (0.9, 1.1, 1.3)
T_CD = (2.3, 3.3, 4.3)                              # 3・2・1
T_MOVE, T_GO = 5.0, 5.4
CARD_W, CARD_H = 900.0, 600.0
CARD_X = 110.0
CARD_H_FINAL = 730.0                                 # 動かしたあと 縦に伸ばす（下を使い切る）
CARD_Y_INTRO, CARD_Y_FINAL = 845.0, 625.0
CD_X, CD_Y = 790.0, 975.0
RUN_DUR = 8.0                                       # 見本の合戦（秒）


def setup():
    global T_SH0, T_HEND, T_D0, T_D1, T_DN, T_DN2, T_REV, T_ANS2, T_TW, T_TS1, T_TW2, T_Q, DURATION, SCENES
    T_SH0 = T_GO + 0.5                              # 合戦の始まり
    T_HEND = T_SH0 + RUN_DUR                        # 見本の合戦が終わる
    T_D0 = T_HEND + 3.2                             # 1万回の図へ
    T_D1 = T_D0 + 0.8 + 3.4                         # 棒が積み終わる
    T_DN = T_D1 + 0.1                               # 数字1（勝った回）
    T_DN2 = T_DN + 3.0                              # 数字2（ばらつき）
    T_REV = T_DN2 + 3.4                             # 答え
    T_ANS2 = T_REV + 2.8                            # 理由
    T_TW = T_ANS2 + 3.4                             # ひねり
    T_TS1 = T_TW + 0.8 + 1.8                        # 棒が伸び終わる
    T_TW2 = T_TW + 4.2                              # ひねりの答え
    T_Q = T_TW2 + 4.2                               # 締め
    DURATION = T_Q + 5.6
    SCENES = [("見本の1回の合戦", T_GO, T_D0), ("1万回の結果（答え・理由）", T_D0, T_TW),
              ("ひねり（条件をかえる）", T_TW, T_Q), ("締め", T_Q, DURATION)]


setup()


def fmt(n):
    return f"{int(round(n)):,}"


def p1(x):
    return f"{math.floor(x * 1000 + 0.5) / 10:.1f}%"


def once_in(f):
    """割合 f（0〜1）→ 約N回に1回"""
    v = 1.0 / f
    return f"約{v:.1f}回に1回" if v < 10 else f"約{int(round(v))}回に1回"


def clock_text(h):
    """時刻（時・小数）→ 午前9時46分／正午／午後1時05分"""
    m = int(round(h * 60))
    hh, mm = divmod(m, 60)
    if hh == 12 and mm == 0:
        return "正午"
    ap = "午前" if hh < 12 else "午後"
    h12 = hh if hh <= 12 else hh - 12
    return f"{ap}{h12}時{mm:02d}分"


# ---------- 絵: 共通 ----------

def _stroke(ctx, w=3.0, col=INK, a=0.9):
    ctx.set_source_rgba(*hexrgb(col, a))
    ctx.set_line_width(w)
    ctx.stroke()


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


# ---------- 地図 ----------
# 旗を立てる位置（カード内の px・旗ざおの根もと）。上が北。西軍は左（西）、東軍は右（東）に置く。
HOME = {
    "ISHI": (95, 195), "SHIM": (195, 262), "KONI": (95, 335), "UKIT": (205, 405), "OTAN": (95, 485),
    "KOBA": (445, 510), "FOUR": (385, 455), "MORI": (665, 470), "CHOS": (570, 500),
    "KURO": (335, 190), "KATO": (480, 232), "II": (335, 305), "FUKU": (335, 405),
    "TODO": (215, 510), "TERA": (320, 515), "IEYA": (625, 265), "IKED": (590, 385),
}
ANCHOR = {0: (265, 225), 1: (275, 355), 2: (300, 480), 3: (720, 450)}          # 戦線のまんなか（移ってきた隊が立つ）

_MAP = {}


def terrain():
    """地図の下絵（盆地・山・川・街道）を一度だけ作る"""
    if "s" in _MAP:
        return _MAP["s"]
    s = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(CARD_W), int(CARD_H))
    c = cairo.Context(s)
    c.set_source_rgb(*hexrgb("#ece6c6")[:3])
    c.paint()
    c.save()                                                        # 盆地のうすい緑
    c.translate(CARD_W / 2, 330)
    c.scale(1.0, 0.52)
    c.arc(0, 0, 450, 0, 2 * math.pi)
    c.restore()
    c.set_source_rgba(*hexrgb("#dfe7bd", 0.9))
    c.fill()
    rng = np.random.default_rng(3)                                   # 北と南の山なみ
    for y0, up in ((98, 1), (CARD_H - 50, -1)):
        c.move_to(0, y0 - up * 80)
        for i, x in enumerate(np.linspace(0, CARD_W, 22)):
            c.line_to(x, y0 + up * (8 + 14 * math.sin(i * 1.3) + rng.uniform(-5, 5)))
        c.line_to(CARD_W, y0 - up * 80)
        c.close_path()
        c.set_source_rgba(*hexrgb("#bfae7e", 0.85))
        c.fill()
    for cx, cy, rx, ry in ((92, 185, 78, 62), (160, 425, 92, 78), (440, 540, 100, 58), (690, 500, 120, 85), (620, 300, 52, 34)):
        for k, col in enumerate(("#d3c291", "#c4b27c", "#b4a068", "#a38f58")):
            c.save()
            c.translate(cx, cy)
            c.scale(1.0, ry / rx)
            c.arc(0, 0, rx * (1 - 0.22 * k), 0, 2 * math.pi)
            c.restore()
            c.set_source_rgba(*hexrgb(col, 0.95))
            c.fill_preserve()
            _stroke(c, 1.6, "#7a6540", 0.5)
    c.move_to(300, 100)                                              # 藤古川（青）
    c.curve_to(250, 220, 390, 330, 330, 540)
    _stroke(c, 7, "#a9d3e8", 0.95)
    c.move_to(0, 372)                                                # 街道（点線）
    c.curve_to(250, 340, 600, 392, CARD_W, 340)
    c.set_dash([14, 9])
    _stroke(c, 4.5, "#a5834f", 0.85)
    c.set_dash([])
    _MAP["s"] = s
    return s


HILL_LABEL = (("笹尾山", 215, 132), ("天満山", 100, 375), ("松尾山", 330, 575), ("南宮山", 705, 562), ("桃配山", 540, 300))


# ---------- 旗 ----------

def draw_flag(ctx, x, y, sc, col, dark, a=1.0, ph=0.0):
    """幟（のぼり）。x, y は旗ざおの根もと。sc は大きさ（兵の数のめやす）"""
    if a <= 0 or sc <= 0:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.push_group()
    ctx.save()
    ctx.scale(1.0, 0.35)
    ctx.arc(0, 4, 17 * sc, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(0.15, 0.12, 0.08, 0.20)
    ctx.fill()
    Hh, Ww, Hb = 66 * sc, 44 * sc, 54 * sc
    ctx.move_to(0, 0)
    ctx.line_to(0, -Hh)
    _stroke(ctx, max(3.0, 4.0 * sc), "#5a4127", 1.0)
    ctx.arc(0, -Hh - 3 * sc, 3.6 * sc, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb("#d6b04a"))
    ctx.fill()
    top = -Hh + 3 * sc
    w1, w2 = 4.5 * sc * math.sin(ph * 2.3), 4.5 * sc * math.sin(ph * 2.3 + 1.4)
    ctx.new_path()
    ctx.move_to(2 * sc, top)
    ctx.curve_to(Ww * 0.4, top + w1, Ww * 0.75, top - w1, Ww + w1, top + 1.5 * w2)
    ctx.line_to(Ww + w2, top + Hb + 2 * w1)
    ctx.curve_to(Ww * 0.75, top + Hb - w2, Ww * 0.4, top + Hb + w2, 2 * sc, top + Hb)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(col))
    ctx.fill_preserve()
    _stroke(ctx, max(2.2, 3.0 * sc), dark, 1.0)
    ctx.move_to(7 * sc, top + 7 * sc)                                # 白い縁取り（内側）
    ctx.line_to(Ww - 6 * sc, top + 7 * sc)
    ctx.move_to(7 * sc, top + Hb - 7 * sc)
    ctx.line_to(Ww - 6 * sc, top + Hb - 7 * sc)
    _stroke(ctx, max(1.6, 2.2 * sc), "#ffffff", 0.85)
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(a)
    ctx.restore()


def draw_burst(ctx, x, y, r, ph):
    """ぶつかり合いの印（星）。血の表現はしない"""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(ph * 0.7)
    for rr, col, a in ((r, "#ffd34a", 0.95), (r * 0.62, "#fff3b0", 1.0)):
        ctx.new_path()
        for i in range(16):
            ang = i * math.pi / 8
            rad = rr if i % 2 == 0 else rr * 0.5
            ctx.line_to(math.cos(ang) * rad, math.sin(ang) * rad)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.fill_preserve()
        if rr == r:
            _stroke(ctx, 2.2, "#d9822b", 0.9)
    ctx.restore()


# ---------- 見本の合戦の時間軸 ----------
_TL = {}


def timeline():
    """見本の記録を、動画の時間で引ける形にする。状態 X_0（始まり）〜 X_m（決着）"""
    if _TL:
        return _TL
    S = samples()
    rec, D1 = S["rec"], S["D1"]
    tr = rec["trace"]
    m = len(tr)
    Sarr = np.zeros((m + 1, U))
    Sarr[0] = rec["S0"]
    fr = np.zeros((m + 1, U), np.int8)
    fr[0] = FRONT0
    rt = np.zeros((m + 1, U), bool)
    act = np.zeros((m + 1, U), bool)
    for k, t_ in enumerate(tr):
        Sarr[k + 1] = t_["S"]
        fr[k + 1] = t_["front"]
        rt[k + 1] = t_["routed"]
        act[k + 1] = t_["active"]
    act[0] = tr[0]["active"]
    events = []                                                      # (τ, 隊の番号のリスト)
    for k, t_ in enumerate(tr):
        if t_["rout"]:
            events.append(((k + 1) * DT, [u for u, _ in t_["rout"]]))
    _TL.update(m=m, tot=m * DT, S=Sarr, fr=fr, rt=rt, act=act, events=events, t0=float(rec["t0"][0]),
               N=D1["N"][0], part=participation(2), win=int(rec["win"][0]), lw=float(rec["loss_w"][0]), le=float(rec["loss_e"][0]))
    return _TL


def tau_of(t):
    """動画の秒 → 合戦の時刻（t0 からの時間）"""
    T = timeline()
    return clamp01((t - T_SH0) / RUN_DUR) * T["tot"]


def sim_state(t):
    T = timeline()
    tau = tau_of(t)
    x = tau / DT
    i = min(int(x), T["m"] - 1)
    u_ = x - i
    Sx = T["S"][i] * (1 - u_) + T["S"][i + 1] * u_
    return dict(tau=tau, i=i, S=Sx)


def unit_pos(u, tau):
    """隊 u の旗の位置（戦線を移るときは 1時間ほどかけて ゆっくり動く）"""
    T = timeline()
    i = min(int(tau / DT), T["m"])
    fr = T["fr"][:, u]
    cur = int(fr[i])
    j = i
    while j > 0 and fr[j - 1] == cur:
        j -= 1

    def tgt(f):
        if f == FRONT0[u] or f < 0:
            return HOME[KEYS[u]]
        ax, ay = ANCHOR[f]
        off = -52 if SIDE0[u] == 0 else 52
        return (ax + off, ay + ((u * 7) % 5 - 2) * 26)
    if j == 0:
        return tgt(cur)
    prev, now = tgt(int(fr[j - 1])), tgt(cur)
    k = smooth((tau - j * DT) / (TRAVEL + DT))
    return (prev[0] + (now[0] - prev[0]) * k, prev[1] + (now[1] - prev[1]) * k)


def flag_color(u):
    if GRP[u] == "d":
        return C_DEF, C_DEF_D
    return (C_WEST, C_WEST_D) if SIDE0[u] == 0 else (C_EAST, C_EAST_D)


def flag_scale(u, Sx):
    T = timeline()
    s0 = max(T["S"][0][u], 1.0)
    base = 0.78 + 0.62 * math.sqrt(min(s0 / 12000.0, 1.0))
    return base * (0.36 + 0.64 * math.sqrt(max(Sx, 0.0) / s0))


def draw_map_content(ctx, t, Hc=CARD_H):
    """カードの中身（地図・旗・ぶつかり）。t は動画の秒"""
    ky = Hc / CARD_H
    ctx.save()
    ctx.scale(1.0, ky)
    ctx.set_source_surface(terrain(), 0, 0)
    ctx.paint()
    ctx.restore()
    for nm, hx, hy in HILL_LABEL:
        text(ctx, nm, hx, hy * ky, 24, "#6d5732", bold=False, alpha=0.95)
    T = timeline()
    running = t >= T_SH0
    st = sim_state(t)
    tau = st["tau"]
    if running and t < T_HEND:                                       # ぶつかり合い（同じ戦線に 西軍・東軍の動いている隊がいる間）
        i = min(int(tau / DT), T["m"])
        act = T["act"][i]
        for f in range(4):
            members = [u for u in range(U) if T["fr"][i][u] == f and act[u] and st["S"][u] > 1.0]
            ws = [unit_pos(u, tau) for u in members if SIDE0[u] == 0]
            es = [unit_pos(u, tau) for u in members if SIDE0[u] == 1]
            if ws and es:
                cx_ = (np.mean([p[0] for p in ws]) + np.mean([p[0] for p in es])) / 2
                cy_ = ((np.mean([p[1] for p in ws]) + np.mean([p[1] for p in es])) / 2 - 28) * ky
                draw_burst(ctx, cx_, cy_, 26 + 5 * math.sin(t * 9 + f), t * 3 + f)
    order = sorted(range(U), key=lambda u: unit_pos(u, tau)[1])      # 北の隊から先に描く
    for u in order:
        px, py = unit_pos(u, tau)
        py *= ky
        part = bool(T["part"][u])
        Sx = float(st["S"][u]) if running else float(T["S"][0][u])
        col, dark = flag_color(u)
        a = 1.0
        if not part:
            col, dark = (C_WEST_L if SIDE0[u] == 0 else C_EAST_L), "#9a8f7a"
        sc = flag_scale(u, Sx if part else float(T["S"][0][u]))
        gone = running and part and Sx < 1.0
        if gone:
            a = 0.45
        draw_flag(ctx, px, py, sc, col, dark, a, ph=t * 3 + u)
        text(ctx, UNITS[u][1], min(max(px + 20 * sc, 66), CARD_W - 70), py + 22, 24, INK if part else PENCIL, alpha=0.55 if gone else (1.0 if part else 0.8))
    rrect(ctx, 14, 14, CARD_W - 28, 84, 14)                          # 数と時計の帯
    ctx.set_source_rgba(*hexrgb(PAPER, 0.95))
    ctx.fill()
    if running:
        sw = sum(float(st["S"][u]) for u in range(U) if SIDE0[u] == 0 and T["part"][u])
        se = sum(float(st["S"][u]) for u in range(U) if SIDE0[u] == 1 and T["part"][u])
        clk = clock_text(T["t0"] + tau)
    else:
        sw = sum(float(T["S"][0][u]) for u in range(U) if SIDE0[u] == 0 and T["part"][u])
        se = sum(float(T["S"][0][u]) for u in range(U) if SIDE0[u] == 1 and T["part"][u])
        clk = "戦いの前"
    text(ctx, "西軍", 40, 40, 26, C_WEST, align="left")
    text(ctx, f"{fmt(sw)}人", 104, 40, 34, C_WEST_D, align="left")
    text(ctx, "東軍", CARD_W - 330, 40, 26, C_EAST, align="left")
    text(ctx, f"{fmt(se)}人", CARD_W - 266, 40, 34, C_EAST_D, align="left")
    text(ctx, clk, CARD_W / 2, 40, 28, INK, bold=True)
    text(ctx, "戦う兵の数（様子見の兵はのぞく）", CARD_W / 2, 76, 24, PENCIL, bold=False)
    msg = None                                                       # 出来事の札（崩れた隊・決着）
    if running:
        for te, us in T["events"]:
            tv = T_SH0 + te / T["tot"] * RUN_DUR
            if tv <= t < tv + 1.5:
                msg = "・".join(UNITS[u][1] for u in us) + "が崩れる"
        if T_SH0 <= t < T_SH0 + 1.4:
            msg = "戦いが始まる"
        if t >= T_HEND - 0.2:
            msg = "西軍の勝ち" if T["win"] == 0 else "東軍の勝ち" if T["win"] == 1 else "決着なし"
    if msg:
        sz = 34
        w_ = core.text_width(msg, sz) + 44
        rrect(ctx, CARD_W / 2 - w_ / 2, 108, w_, 52, 12)
        ctx.set_source_rgba(*hexrgb("#fff0a0", 0.96))
        ctx.fill()
        text(ctx, msg, CARD_W / 2, 134, sz, RED if t >= T_HEND - 0.2 else INK)
    ly = Hc - 34                                                 # 色の見本（下）
    rrect(ctx, 20, ly - 24, 600, 46, 10)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.93))
    ctx.fill()
    xx = 34.0
    for col, dark, lab in ((C_WEST, C_WEST_D, "西軍"), (C_EAST, C_EAST_D, "東軍"), (C_DEF, C_DEF_D, "寝返りの隊"), (C_WEST_L, "#9a8f7a", "動かない隊")):
        draw_flag(ctx, xx + 8, ly + 16, 0.36, col, dark, 1.0)
        text(ctx, lab, xx + 36, ly, 24, INK, align="left", bold=False)
        xx += 36 + core.text_width(lab, 24, bold=False) + 30


def draw_card(ctx, t, m):
    x0 = CARD_X
    y0 = CARD_Y_INTRO + (CARD_Y_FINAL - CARD_Y_INTRO) * m
    Hc = CARD_H + (CARD_H_FINAL - CARD_H) * m
    ctx.save()
    ctx.translate(x0, y0)
    rrect(ctx, 0, 0, CARD_W, Hc, 20)
    ctx.set_source_rgba(*hexrgb(PAPER, 0.97))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.75)
    ctx.save()
    rrect(ctx, 10, 10, CARD_W - 20, Hc - 20, 14)
    ctx.clip()
    draw_map_content(ctx, t, Hc)
    ctx.restore()
    rrect(ctx, 10, 10, CARD_W - 20, Hc - 20, 14)
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
    T = timeline()
    if T_GO <= t < T_HEND + 0.2:
        s_ = ease_out((t - T_GO) / 0.3)
        note.sticky(ctx, "たとえば、この1回の合戦では", 580, 1418, 34, "mint", a=s_, tilt=0.02)
    if t >= T_HEND + 0.2:
        s_ = ease_out((t - T_HEND - 0.2) / 0.3) * (1 - ease((t - T_D0) / 0.25))
        who = {0: "西軍の勝ち", 1: "東軍の勝ち", 2: "決着なし"}[T["win"]]
        note.sticky(ctx, f"この1回では {who}（損失 西{pct(T['lw'])}%・東{pct(T['le'])}%）", 545, 1418, 30, "yellow", a=s_, tilt=0.02)


# ---------- 1万回の図（損失の差の山） ----------
NB = 40
N_CK = 100
HX0, HX1 = 150.0, 960.0
HB, HMAX = 1000.0, 270.0
_HIST = {}


def hist_data():
    """損失の差 d（西軍の損失 − 東軍の損失）を 40の箱に。1万回のうち最初の m 回までの積み上げを 100段階で持つ"""
    if _HIST:
        return _HIST
    res = results()["res"][2]
    d, w = res["d"], res["win"]
    b = np.clip(((d + 1) / 2 * NB).astype(int), 0, NB - 1)
    cum = np.zeros((N_CK + 1, NB, 3))
    c = np.zeros((NB, 3))
    prev = 0
    for k in range(1, N_CK + 1):
        m = int(round(N_TRIAL * k / N_CK))
        np.add.at(c, (b[prev:m], w[prev:m]), 1)
        prev = m
        cum[k] = c
    _HIST.update(cum=cum, b=b, vmax=float(cum[-1].sum(1).max()))
    return _HIST


def hist_alpha(t):
    if t < T_D0:
        return 0.0
    return ease((t - T_D0) / 0.35) * (1 - ease((t - T_TW + 0.1) / 0.3))


def draw_hist(ctx, t):
    a = hist_alpha(t)
    if a <= 0:
        return
    r = results()
    s2 = r["st"][2]
    hd = hist_data()
    pr = clamp01((t - T_D0 - 0.8) / (T_D1 - T_D0 - 0.8))
    k = N_CK if pr >= 1 else int(N_CK * ease(pr))
    text(ctx, "1万回の合戦（寝返りなし）", 580, 655, 40, INK, alpha=a)
    text(ctx, f"棒＝その損失の差になった回数　{fmt(N_TRIAL * k / N_CK)} / 10,000 回目", 580, 700, 26, PENCIL, bold=False, alpha=a)
    bw = (HX1 - HX0) / NB
    cols = (C_WEST, C_EAST, C_NONE)
    for j in range(NB):
        y = HB
        for c_ in range(3):
            v = hd["cum"][k][j][c_]
            if v <= 0:
                continue
            hgt = HMAX * v / hd["vmax"]
            ctx.rectangle(HX0 + j * bw + 1, y - hgt, bw - 2, hgt)
            ctx.set_source_rgba(*hexrgb(cols[c_], 0.92 * a))
            ctx.fill()
            y -= hgt
    ctx.move_to(HX0 - 6, HB)
    ctx.line_to(HX1 + 6, HB)
    _stroke(ctx, 3, INK, 0.7 * a)
    xm = HX0 + (HX1 - HX0) / 2
    ctx.move_to(xm, HB + 4)
    ctx.line_to(xm, HB - HMAX - 10)
    ctx.set_dash([8, 7])
    _stroke(ctx, 2.5, PENCIL, 0.7 * a)
    ctx.set_dash([])
    text(ctx, "← 西軍が有利", 260, 1038, 28, C_WEST_D, alpha=a)
    text(ctx, "同じくらい", xm, 1038, 26, PENCIL, bold=False, alpha=a)
    text(ctx, "東軍が有利 →", 815, 1038, 28, C_EAST_D, alpha=a)
    if t >= T_D0 + 0.8:                                              # 勝った回の数は 棒が積まれるのと一緒に増える
        u = ease_out((t - T_D0 - 0.8) / 0.3) * a
        cs = hd["cum"][k].sum(0)
        for cx_, lab, n_, col in ((265, "西軍が勝った回", cs[0], C_WEST_D), (545, "決着なし", cs[2], PENCIL), (815, "東軍が勝った回", cs[1], C_EAST_D)):
            text(ctx, lab, cx_, 1093, 28, INK, bold=False, alpha=u)
            text(ctx, f"{fmt(n_)}回", cx_, 1150, 54, col, alpha=u)
    if t >= T_DN2:
        u = ease_out((t - T_DN2) / 0.3) * a
        lines_a = 1 - ease((t - T_ANS2) / 0.3)
        res = r["res"][2]
        text(ctx, f"西軍が勝つのは {once_in(s2['p'])}／東軍は {once_in(s2['q'])}", 545, 1212, 28, INK, alpha=u * lines_a)
        bi, wi = s2["best"], s2["worst"]
        text(ctx, f"いちばん西軍に良い回: 西軍の損失 {pct(res['loss_w'][bi])}%・東軍 {pct(res['loss_e'][bi])}%", 580, 1250, 28, C_WEST_D, bold=False, alpha=u * lines_a)
        text(ctx, f"いちばん悪い回: 西軍の損失 {pct(res['loss_w'][wi])}%・東軍 {pct(res['loss_e'][wi])}%", 580, 1288, 28, C_EAST_D, bold=False, alpha=u * lines_a)


# ---------- ひねり（条件をかえる） ----------
TW_X = (250.0, 530.0, 805.0)
TW_BASE, TW_H = 1060.0, 350.0


def tw_alpha(t):
    if t < T_TW:
        return 0.0
    return ease((t - T_TW) / 0.35) * (1 - ease((t - T_Q + 0.1) / 0.3))


TW_LABELS = ("①史実どおり\n（東軍に寝返る）", "②西軍のまま\n戦う", "③様子見のまま\n動かない")


def draw_twist(ctx, t):
    a = tw_alpha(t)
    if a <= 0:
        return
    st = results()["st"]
    text(ctx, "寝返った隊の動きをかえて、1万回ずつ", 580, 655, 38, INK, alpha=a)
    text(ctx, "西軍が勝った回の割合", 580, 700, 26, PENCIL, bold=False, alpha=a)
    ctx.move_to(130, TW_BASE)
    ctx.line_to(960, TW_BASE)
    _stroke(ctx, 3, INK, 0.7 * a)
    pr = ease(clamp01((t - T_TW - 0.8) / (T_TS1 - T_TW - 0.8)))
    for i, c in enumerate(CONDS):
        v = st[c]["p"]
        x = TW_X[i]
        hgt = TW_H * v * pr
        rrect(ctx, x - 70, TW_BASE - hgt, 140, max(hgt, 1.0), 8)
        ctx.set_source_rgba(*hexrgb(C_WEST if c != 2 else "#e0605a", 0.92 * a))
        ctx.fill()
        text(ctx, f"{pct(v * pr)}%", x, TW_BASE - hgt - 32, 44, RED, alpha=a)
        text(ctx, TW_LABELS[i], x, TW_BASE + 54, 26, INK, bold=False, alpha=a)


TW_Q = "では、寝返らずに\n様子見のままだったら？"


def tw_a():
    st = results()["st"]
    return f"西軍が勝つ割合は ①{pct(st[1]['p'])}%・②{pct(st[2]['p'])}%・③{pct(st[4]['p'])}%。"


def tw_b():
    st = results()["st"]
    return f"様子見のままなら、東軍が約{pct(st[4]['q'])}%で勝つ。"


def tw_c():
    return "寝返った隊の動き方しだいで、勝つ側が逆になる。"


# ---------- 答え ----------

def answer_key():
    return results()["key"]


def reason_text():
    s = results()["st"][2]
    return f"失った兵は 西軍{pct(s['med_lw'])}%・東軍{pct(s['med_le'])}%。\n（中央値＝1万回のちょうど真ん中の値）"


def draw_answer(ctx, t):
    if t < T_REV:
        return
    key = answer_key()
    b = ease_out((t - T_REV - 0.15) / 0.3)
    r_a = 1 - ease((t - T_TW) / 0.3) if t >= T_TW else 1.0
    note.sticky(ctx, f"正解は『{KEY_LABEL[key]}』。", 570, 1362, 38, "yellow", fg=RED, a=b * r_a, tilt=-0.02)
    if t >= T_ANS2 and r_a > 0:
        c = ease_out((t - T_ANS2) / 0.3) * r_a
        note.sticky(ctx, reason_text(), 570, 1240, 30, "blue", a=c, tilt=0.012)
    if t >= T_TW:
        d = ease_out((t - T_TW - 0.15) / 0.3)
        note.sticky(ctx, TW_Q, 570, 1236, 40, "pink", fg=RED, a=d, tilt=-0.015)
    if t >= T_TW2:
        e = ease_out((t - T_TW2) / 0.3)
        # 2026-11-08 統括の指示: tw_a（①②③の割合）はすぐ上のグラフと同じなので画面に出さない
        text(ctx, tw_b(), 545, 1362, 34, RED, alpha=e)
        text(ctx, tw_c(), 545, 1408, 28, INK, bold=False, alpha=e)


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
    return 100.0 * max_w / max(core.text_width(l, 100.0) for l in BIG_Q3)


class SIntro(note.Intro):
    """この回だけの冒頭。上: 問い3行（横幅いっぱい・同じ大きさ）・三択（横1列）。その下に関ヶ原の地図（0秒目から旗がゆれ、場面が寄った所から引く）"""
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
            text(ctx, DETAIL_RULE, 565, 722, 30, INK, bold=False, alpha=a1)
            text(ctx, DETAIL, 565, 758, 26, PENCIL, bold=False, alpha=a1)
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
                note.pen_circle(ctx, x0 + (58 + vw) / 2, y, (58 + vw) / 2 + 24, 38, RED, seed=31, width=7, progress=rev)
            elif rev > 0:
                note.pen_line(ctx, x0 - 8, y + 4, x0 + 66 + vw, y - 2, PENCIL, seed=i + 40, width=4, progress=rev, alpha=0.8)

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


# ---------- 締め（二人の武将） ----------

def draw_busho(ctx, x, yb, h, side, t, ph=0.0):
    """鎧の武者（足もとが (x, yb)、高さ h）。side 0 = 西軍（右向き）、1 = 東軍（左向き）。旗ざおを片手で持つ"""
    k = h / 520.0
    d = 1.0 if side == 0 else -1.0
    arm = "#b73a34" if side == 0 else "#2c5aa0"
    arm_d = "#6c1f1b" if side == 0 else "#17325f"
    lace, dk, skin = "#f1e2b4", "#2d2a33", "#f0c9a0"
    bob = 2.0 * math.sin(t * 1.6 + ph)
    ctx.save()
    ctx.translate(x, yb)
    ctx.scale(d * k, k)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    def poly(pts, col, w=4.0, a=1.0):
        ctx.new_path()
        ctx.move_to(*pts[0])
        for p_ in pts[1:]:
            ctx.line_to(*p_)
        ctx.close_path()
        ctx.set_source_rgba(*hexrgb(col, a))
        ctx.fill_preserve()
        _stroke(ctx, w, INK, 0.9)
    # 奥の腕（体の後ろ側へ下ろす）
    ctx.move_to(80, -330 + bob)
    ctx.line_to(96, -250 + bob)
    ctx.line_to(84, -205 + bob)
    _stroke(ctx, 34, arm_d, 1.0)
    ctx.arc(84, -196 + bob, 17, 0, 2 * math.pi)
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    # 足（はかま・すね当て・わらじ）
    for sx in (-1, 1):
        poly([(sx * 8, -225), (sx * 56, -225), (sx * 62, -22), (sx * 14, -22)], "#3d4457")
        poly([(sx * 16, -125), (sx * 58, -125), (sx * 60, -30), (sx * 18, -30)], "#a3a9b6", 3.0)
        ctx.save()
        ctx.translate(sx * 38, -12)
        ctx.scale(1.0, 0.4)
        ctx.arc(0, 0, 32, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(*hexrgb("#b49a62"))
        ctx.fill_preserve()
        _stroke(ctx, 3, INK, 0.85)
    # 草摺（腰の板）
    for i in range(6):
        x0 = -90 + i * 30
        poly([(x0, -250), (x0 + 30, -250), (x0 + 28, -170), (x0 + 2, -170)], arm, 3.0)
        ctx.move_to(x0 + 15, -246)
        ctx.line_to(x0 + 15, -176)
        _stroke(ctx, 2.0, lace, 0.8)
    # 胴
    poly([(-84, -345 + bob), (84, -345 + bob), (70, -245), (-70, -245)], arm, 4.5)
    for yy in (-318, -292, -266):
        ctx.move_to(-76 + (yy + 318) * -0.15, yy + bob * 0.5)
        ctx.line_to(76 - (yy + 318) * -0.15, yy + bob * 0.5)
        _stroke(ctx, 3.0, lace, 0.85)
    ctx.move_to(0, -343 + bob)
    ctx.line_to(0, -247)
    _stroke(ctx, 3.0, arm_d, 0.9)
    poly([(-30, -345 + bob), (30, -345 + bob), (38, -300), (-38, -300)], dk, 3.5)               # 胸板
    # 首
    ctx.rectangle(-14, -372 + bob, 28, 34)
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill()
    # 袖（肩の板）
    for sx in (-1, 1):
        for j in range(3):
            poly([(sx * 78 - 38 + j * 0, -352 + j * 24 + bob), (sx * 78 + 38, -352 + j * 24 + bob),
                  (sx * 78 + 34, -330 + j * 24 + bob), (sx * 78 - 34, -330 + j * 24 + bob)], arm if j != 1 else arm_d, 3.2)
    # 旗ざお（外側の腕。旗は外へなびく）
    ctx.save()
    ctx.scale(-1.0, 1.0)
    px_ = 138.0
    ctx.move_to(px_, -4)
    ctx.line_to(px_, -540)
    _stroke(ctx, 9, "#6b4a2b", 1.0)
    fl_col = "#c9423c" if side == 0 else "#2f6cb3"
    fl_dk = "#7e231f" if side == 0 else "#173f73"
    wv = 5 * math.sin(t * 3 + ph)
    ctx.new_path()                                                  # 幟
    ctx.move_to(px_ + 5, -535)
    ctx.curve_to(px_ + 40, -535 + wv, px_ + 70, -535 - wv, px_ + 92 + wv, -535)
    ctx.line_to(px_ + 92 - wv, -295)
    ctx.curve_to(px_ + 70, -295 + wv, px_ + 40, -295 - wv, px_ + 5, -295)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(fl_col))
    ctx.fill_preserve()
    _stroke(ctx, 4.5, fl_dk, 1.0)
    ctx.move_to(px_ + 14, -523)
    ctx.line_to(px_ + 82, -523)
    ctx.move_to(px_ + 14, -307)
    ctx.line_to(px_ + 82, -307)
    _stroke(ctx, 2.6, "#ffffff", 0.85)
    ctx.move_to(78 * 1.0, -330 + bob)                               # 手前の腕（肩 → ひじ → 旗ざおの手）
    ctx.line_to(112, -300 + bob)
    ctx.line_to(px_, -360 + bob)
    _stroke(ctx, 34, arm_d, 1.0)
    ctx.move_to(112, -300 + bob)
    ctx.line_to(px_ - 6, -352 + bob)
    _stroke(ctx, 28, arm, 1.0)
    ctx.arc(px_, -366 + bob, 18, 0, 2 * math.pi)                    # こぶし（旗ざおの手前に重ねて握る）
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 3.5, INK, 0.9)
    for j in range(3):
        ctx.move_to(px_ - 12, -376 + j * 10 + bob)
        ctx.line_to(px_ + 14, -376 + j * 10 + bob)
        _stroke(ctx, 3.0, "#b98a62", 0.9)
    ctx.restore()
    # 頭
    hx, hy = 6.0, -398.0 + bob
    ctx.save()
    ctx.translate(hx, hy)
    ctx.scale(1.0, 1.15)
    ctx.arc(0, 0, 38, 0, 2 * math.pi)
    ctx.restore()
    ctx.set_source_rgba(*hexrgb(skin))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    for ex in (-9, 20):                                              # 目（内側＝右を見る）
        ctx.save()
        ctx.translate(hx + ex, hy + 4)
        ctx.scale(0.8, 1.0)
        ctx.arc(0, 0, 8, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.fill_preserve()
        _stroke(ctx, 2.5, INK, 0.9)
        ctx.arc(hx + ex + 3, hy + 5, 4, 0, 2 * math.pi)
        ctx.set_source_rgba(*hexrgb(INK))
        ctx.fill()
        ctx.move_to(hx + ex - 11, hy - 8)
        ctx.line_to(hx + ex + 10, hy - 14)
        _stroke(ctx, 5, dk, 0.95)
    ctx.move_to(hx + 22, hy + 14)                                    # 鼻
    ctx.curve_to(hx + 28, hy + 22, hx + 26, hy + 26, hx + 18, hy + 26)
    _stroke(ctx, 3, INK, 0.8)
    ctx.move_to(hx - 14, hy + 34)                                    # 口とひげ
    ctx.curve_to(hx - 2, hy + 38, hx + 10, hy + 38, hx + 20, hy + 33)
    _stroke(ctx, 3.5, INK, 0.9)
    ctx.move_to(hx - 12, hy + 28)
    ctx.curve_to(hx - 4, hy + 24, hx + 6, hy + 24, hx + 16, hy + 28)
    _stroke(ctx, 3, dk, 0.9)
    # 兜
    poly([(hx - 60, hy - 2), (hx - 44, hy + 40), (hx - 30, hy + 36), (hx - 28, hy - 6)], arm_d, 3.5)     # 錣（首まわり）
    poly([(hx + 60, hy - 2), (hx + 44, hy + 40), (hx + 30, hy + 36), (hx + 28, hy - 6)], arm_d, 3.5)
    ctx.new_path()
    ctx.move_to(hx - 46, hy - 6)
    ctx.curve_to(hx - 48, hy - 78, hx + 48, hy - 78, hx + 46, hy - 6)
    ctx.close_path()
    ctx.set_source_rgba(*hexrgb(dk))
    ctx.fill_preserve()
    _stroke(ctx, 4, INK, 0.95)
    ctx.move_to(hx - 48, hy - 10)
    ctx.line_to(hx + 48, hy - 10)
    _stroke(ctx, 7, "#d6b04a", 1.0)
    ctx.arc(hx, hy - 38, 28, math.pi * 1.15, math.pi * 1.85)           # 前立て（三日月）
    _stroke(ctx, 7, "#d6b04a", 1.0)
    ctx.restore()
    return (x - d * (138 + 46) * k, yb - 415 * k)                    # 旗の中心（文字を重ねる位置）


def draw_closing(ctx, t):
    q = ease_out((t - T_Q) / 0.35) if t >= T_Q else 0.0
    if q <= 0:
        return
    note.sticky(ctx, "勝ち負けを分けたのは、\n寝返った隊が戦ったかどうか", 570, 672, 46, "yellow", a=q, tilt=-0.02)
    r2 = ease_out((t - T_Q - 1.6) / 0.3)
    note.sticky(ctx, "あなたなら、どちらの陣に立ちますか？", 570, 835, 36, "pink", a=r2, tilt=0.015)
    r = ease_out((t - T_Q - 2.4) / 0.3)
    text(ctx, "コメントで教えてください", 570, 925, 30, INK, bold=False, alpha=r)
    ctx.save()
    ctx.push_group()
    ctx.set_source_rgba(*hexrgb("#d9cfa5", 0.9))                     # 足もとの地面
    ctx.rectangle(0, 1470, W, 120)
    ctx.fill()
    ps = []
    for x_, side in ((380, 0), (700, 1)):
        ps.append((draw_busho(ctx, x_, 1540, 560, side, t, ph=side * 1.7), side))
    ctx.pop_group_to_source()
    ctx.paint_with_alpha(q)
    ctx.restore()
    for (fx, fy), side in ps:                                        # 旗の文字（向きがそろうよう、あとから正しい向きで）
        text(ctx, "西" if side == 0 else "東", fx, fy, 60, "#ffffff", alpha=q)


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

def build_audio():
    mx = Mixer(DURATION)
    mx.add(0, pad(DURATION, freqs=(110.0, 164.8, 220.0, 261.6)), 1.0, bgm=True)
    INTRO.audio(mx)
    mx.add(0.0, whoosh(0.6), 0.25)
    for i in range(4):                                      # 冒頭: 太鼓 どん・どん
        mx.add(0.1 + 0.5 * i, thump(0.3), 0.30)
    T = timeline()
    mx.add(T_SH0 - 0.1, riser(0.6), 0.35)
    beat(mx, T_SH0 + 0.3, T_HEND - 0.3, bpm=104, vol=0.35)
    for te, us in T["events"]:                              # 隊が崩れるたびに 低い音
        mx.add(T_SH0 + te / T["tot"] * RUN_DUR, thump(0.4), 0.45)
    mx.add(T_HEND - 0.2, bell(523.3, 1.2), 0.45)
    mx.add(T_D0 - 0.5, riser(0.8), 0.4)                     # 1万回の図
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


def _lanchester_ref():
    """石田（西）と黒田・細川（東）の2隊だけにして、崩れ・運・山の利を消すと ランチェスター（15分刻みの式）どおりに減るか。
    速い計算（simulate）と、1行ずつの普通の式を比べる"""
    UN, SC, NZ = stack_trials(5, 1)
    D = derive(UN, SC, NZ)
    ia, ib = IX["ISHI"], IX["KURO"]
    D["f"][:] = 0.0
    D["f"][0, ia] = D["f"][0, ib] = 1.0
    D["N"][0, ia], D["N"][0, ib] = 8000.0, 6000.0
    D["arr"][:] = 0.0
    D["r"][:] = 2.0
    D["H"][:] = 1.0
    D["beta"][:] = 0.15
    D["nz"][:] = 1.0
    D["t0"][:] = 8.0
    rec = simulate(D, 2, rec=True)
    w, e = 8000.0, 6000.0
    err = 0.0
    for tr in rec["trace"]:
        w, e = w - 0.15 * DT * e, e - 0.15 * DT * w
        err = max(err, abs(tr["S"][ia] - w), abs(tr["S"][ib] - e))
    return err, len(rec["trace"])


def run_checks():
    r = results()
    st, res = r["st"], r["res"]
    s2 = st[2]
    checks = []
    # (1) 条件
    checks.append(("隊は 西9・東8", float(int((SIDE0 == 0).sum()) * 100 + int((SIDE0 == 1).sum())), 908.0, 0.0))
    checks.append(("回数 = 1万（①②④の3条件とも）", float(sum(len(res[c]["win"]) == N_TRIAL for c in CONDS)), 3.0, 0.0))
    checks.append(("勝ち・負け・決着なしの合計 = 1万（条件②）", float(s2["nw"] + s2["ne"] + s2["nz"]), float(N_TRIAL), 0.0))
    D = r["D"]
    checks.append(("乱数: 戦いの始まり t0 の平均が 9時（8〜10の一様）", float(D["t0"].mean()), 9.0, 0.03))
    checks.append(("乱数: β の平均が 0.175（0.10〜0.25の一様）", float(D["beta"].mean()), 0.175, 0.003))
    checks.append(("乱数: H の平均が 1.25（1.0〜1.5の一様）", float(D["H"].mean()), 1.25, 0.01))
    checks.append(("乱数: 宇喜多の兵の数の平均が 範囲の中央", float(D["N"][:, IX["UKIT"]].mean()), (10000 + 17220) / 2, 90.0))
    checks.append(("乱数: 小早川の兵の数の平均が 0.7×15,350＋0.3×7,500", float(D["N"][:, KOBA].mean()), 0.7 * 15350 + 0.3 * 7500, 100.0))
    checks.append(("乱数: 普通の隊の戦う割合の平均 0.8、様子見の傾向の隊 0.65", float(abs(D["f"][:, IX["UKIT"]].mean() - 0.8) < 0.01 and abs(D["f"][:, IX["SHIM"]].mean() - 0.65) < 0.01), 1.0, 0.0))
    # (2) 数え方の整合
    checks.append(("負けた側の失った割合は 50% 以上（決着のついた回すべて）", float(np.all(np.maximum(res[2]["loss_w"], res[2]["loss_e"])[res[2]["win"] != 2] >= 0.5)), 1.0, 0.0))
    checks.append(("決着なしの回は どちらも 50% 未満", float(np.all(np.maximum(res[2]["loss_w"], res[2]["loss_e"])[res[2]["win"] == 2] < 0.5)), 1.0, 0.0))
    chk = np.where(res[2]["loss_w"] >= res[2]["loss_e"], 1, 0)
    dec = res[2]["win"] != 2
    checks.append(("勝ち負けは 失った割合が大きい側が負け（決着のついた回すべて）", float(np.all(res[2]["win"][dec] == chk[dec])), 1.0, 0.0))
    checks.append(("損失の差 d = 西軍の損失 − 東軍の損失（1万回すべて）", float(np.allclose(res[2]["d"], res[2]["loss_w"] - res[2]["loss_e"])), 1.0, 0.0))
    hd = hist_data()
    checks.append(("山の図の箱の合計 = 1万", float(hd["cum"][-1].sum()), float(N_TRIAL), 0.0))
    checks.append(("山の図: 西軍が勝った回の合計 = 数字の札", float(hd["cum"][-1][:, 0].sum()), float(s2["nw"]), 0.0))
    checks.append(("山の図: 東軍が勝った回の合計 = 数字の札", float(hd["cum"][-1][:, 1].sum()), float(s2["ne"]), 0.0))
    # (3) 速い計算と 別の書き方の照合
    err, nst = _lanchester_ref()
    checks.append((f"ランチェスターの式（2隊・{nst}ステップ）: 速い計算と 1行ずつの式の差（人）", err, 0.0, 1e-6))
    UN, SC, NZ = r["UN"][:300], r["SC"][:300], r["NZ"][:300]
    again = simulate(derive(UN, SC, NZ), 2)
    checks.append(("同じ乱数で やり直すと 結果が同じ（最初の300回）", float(np.array_equal(again["win"], res[2]["win"][:300]) and np.allclose(again["d"], res[2]["d"][:300])), 1.0, 0.0))
    one = simulate(derive(r["UN"][5:6], r["SC"][5:6], r["NZ"][5:6]), 2)
    checks.append(("1回だけ回しても 1万回の中の同じ回と同じ結果（#5）", float(one["win"][0] == res[2]["win"][5] and abs(one["d"][0] - res[2]["d"][5]) < 1e-12), 1.0, 0.0))
    # (4) 史実の向き・条件のちがい
    checks.append(("①史実どおりでは 東軍が勝つ回が過半（史実と同じ向き）", float(st[1]["q"] > 0.5), 1.0, 0.0))
    # (5) 答え
    key = answer_by_rule(s2["p"], s2["q"])
    checks.append(("規則の答え = west（西軍が勝つ）", float(key == "west"), 1.0, 0.0))
    checks.append(("画面の正解の記号が、規則の答えの位置と同じ", float(LABELS.index(KEY_LABEL[key])), float(INTRO.correct), 0.0))
    checks.append(("正解の記号が B 以外（A か C）", float(INTRO.correct in (0, 2)), 1.0, 0.0))
    checks.append(("記号の並び: 西軍が勝つ・ほぼ互角・東軍が勝つ の順", float(LABELS == ["西軍が勝つ", "ほぼ互角", "東軍が勝つ"]), 1.0, 0.0))
    for p_, q_, k_ in ((0.60, 0.4, "west"), (0.59, 0.41, "even"), (0.2, 0.6, "east"), (0.5, 0.5, "even")):
        checks.append((f"規則の道具: p={p_:.2f} q={q_:.2f} → {k_}", float(answer_by_rule(p_, q_) == k_), 1.0, 0.0))
    # (6) 見本は1万回の中の1回そのもの
    S = samples()
    h = S["h"]
    rec = S["rec"]
    checks.append(("見本: 記録し直した勝ち負け = 1万回の記録", float(rec["win"][0]), float(res[2]["win"][h]), 0.0))
    checks.append(("見本: 記録し直した西軍の損失 = 1万回の記録", float(rec["loss_w"][0]), float(res[2]["loss_w"][h]), 1e-12))
    checks.append(("見本: 記録し直した東軍の損失 = 1万回の記録", float(rec["loss_e"][0]), float(res[2]["loss_e"][h]), 1e-12))
    checks.append(("見本: 答えの側（西軍）が勝った回", float(rec["win"][0]), 0.0, 0.0))
    T = timeline()
    checks.append(("見本: 画面の最後の勝ち = 1万回の記録", float(T["win"]), float(res[2]["win"][h]), 0.0))
    checks.append(("見本: 旗の大きさの元（兵の数）が減るだけ（増えない）", float(np.all(np.diff(T["S"], axis=0) <= 1e-9)), 1.0, 0.0))
    checks.append(("見本: 兵の数は始まりの数より多くならない", float(np.all(T["S"] <= T["S"][0][None, :] + 1e-9)), 1.0, 0.0))
    # (7) 問い（3行）が収まる
    s3 = min(big3_size(820.0), 92.0)
    checks.append(("問い3行: 文字は24px以上", float(s3 >= 24), 1.0, 0.0))
    checks.append(("問い3行: いちばん長い行が 820px 以内", float(max(core.text_width(l, s3) for l in BIG_Q3) <= 820.5), 1.0, 0.0))
    checks.append(("問い3行: 1行目の上端が iPhone で隠れる y=370 より下", float(432 - s3 / 2 >= 370), 1.0, 0.0))
    wmax = max(core.text_width(l, 100.0) for l in BIG_Q)
    checks.append(("上の問い2行: 文字は24px以上", float(min(56.0, 100.0 * 850.0 / wmax) >= 24), 1.0, 0.0))
    # (8) ひねりの文
    q4 = st[4]["q"]
    checks.append(("ひねり: ④様子見のままでは 東軍が勝つ割合が過半（答えが逆になる）", float(q4 > 0.5), 1.0, 0.0))
    checks.append(("ひねり: ④の東軍が勝つ割合 = 画面の「約N%」", float(pct(q4)), float(int(tw_b().split("約")[1].split("%")[0])), 0.0))
    checks.append(("ひねり: ④の東軍が勝つ割合は 感度の2,500回（約80%）と 5ポイント以内", abs(q4 - 0.80), 0.0, 0.05))
    UN2, SC2, NZ2 = stack_trials(SEED_MAIN + 11, N_TRIAL)
    r4b = simulate(derive(UN2, SC2, NZ2), 4)
    checks.append(("ひねり: 別の乱数の1万回で回し直しても ④の東軍が勝つ割合が ほぼ同じ（±2ポイント。1万回の標準誤差は約0.4ポイント）", abs(float((r4b["win"] == 1).mean()) - q4), 0.0, 0.02))
    checks.append(("ひねり: ④は ①②と同じ乱数（兵の数の違いはなし）で回した（④の回数 = 1万）", float(len(res[4]["win"])), float(N_TRIAL), 0.0))
    checks.append(("ひねり: ①②④の順に 西軍が勝つ割合 ② > ① かつ ② > ④", float(st[2]["p"] > st[1]["p"] and st[2]["p"] > st[4]["p"]), 1.0, 0.0))
    # (9) 場面の長さ
    for nm, a_, b_ in SCENES:
        checks.append((f"場面「{nm}」が 3秒以上（{b_ - a_:.1f}秒）", float(b_ - a_ >= 3.0), 1.0, 0.0))
    checks.append(("見本の合戦の結果が見える時間 3秒以上", float(T_D0 - T_HEND >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: 勝った回の札 3秒以上", float(T_DN2 - T_DN >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: ばらつき 3秒以上", float(T_REV - T_DN2 >= 3.0), 1.0, 0.0))
    checks.append(("数字が見える時間: ひねりの棒グラフ 3秒以上", float(T_Q - T_TS1 >= 3.0), 1.0, 0.0))
    checks.append(("見本の合戦は 1ステップ（15分）が 0.5秒以上", float(RUN_DUR / T["m"] >= 0.5), 1.0, 0.0))
    checks.append(("長さ 45秒前後（43〜49秒）", float(43.0 <= DURATION <= 49.0), 1.0, 0.0))
    # (10) 冒頭の動き
    cf = change_fraction(0.0, 1.0)
    checks.append(("冒頭 0〜1秒で 画面の15%以上が動く", float(cf >= 0.15), 1.0, 0.0))
    check_answers(checks)
    print(f"  冒頭 0〜1秒の変化: {cf:.1%}（0〜0.3秒 {change_fraction(0.0, 0.3):.1%}）")


def lint():
    """mp4 は書かずに、全コマの文字を記録して 公開前チェックと同じ点検をする"""
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
    T = timeline()
    print(f"長さ {DURATION:.1f}秒  合戦 {T_SH0:.1f}〜{T_HEND:.1f}（{T['m']}ステップ）  山の図 {T_D0:.1f}-{T_D1:.1f}  数字 {T_DN:.1f}/{T_DN2:.1f}  答え {T_REV:.1f}  理由 {T_ANS2:.1f}  ひねり {T_TW:.1f}/{T_TW2:.1f}  締め {T_Q:.1f}")
    print("  場面の長さ: " + "  ".join(f"{nm} {b - a:.1f}秒" for nm, a, b in SCENES))
    print(f"  見本: 回 #{S['h']}  始まり {clock_text(T['t0'])}  決着まで {T['tot']:.2f}時間  西軍の損失 {pct(T['lw'])}%・東軍 {pct(T['le'])}%  崩れた隊: " + "、".join("・".join(UNITS[u][1] for u in us) for _, us in T['events']))
    print("  理由:", reason_text().replace("\n", " / "))
    print("  ひねり:", TW_Q.replace("\n", ""), "|", tw_a(), "|", tw_b())
    print("  選択肢:", " / ".join(f"{'ABC'[i]}:{v}" for i, v in enumerate(LABELS)), "正解:", "ABC"[INTRO.correct])


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    report()
    report_full()
    if "--nocheck" not in sys.argv:
        run_checks()
    if "--stills" in sys.argv:
        ts = [0.0, 0.4, 1.0, 2.5, 4.4, 5.2, T_SH0 + 0.5, T_SH0 + 2.0, T_SH0 + 3.5, T_SH0 + 5.0, T_SH0 + 6.5, T_HEND - 0.3,
              T_HEND + 1.5, T_D0 + 1.5, T_D1 - 0.2, T_DN + 1.2, T_DN2 + 1.2, T_REV + 0.9, T_ANS2 + 0.6,
              T_TW + 0.8, T_TW + 2.4, T_TS1 + 1.2, T_TW2 + 0.8, T_Q + 1.5, DURATION - 0.2]
        stills(draw, ts, OUT)
    elif "--lint" in sys.argv:
        lint()
    else:
        render(draw, DURATION, OUT / f"{SLUG}.mp4", build_audio())
        print("完成:", OUT / f"{SLUG}.mp4")
