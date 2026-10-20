# めでたしかめ

YouTube ショート「めでたしかめ」の動画を作っているコードです。
**動画1本 ＝ `sims/` のファイル1つ。** 絵も音も、すべてこのコードが作っています（素材ファイルはありません）。

<img src="brand/icon.png" width="120" alt="めでたしかめ">

## 動かし方

```bash
pip install -r requirements.txt   # ほかに ffmpeg が必要
python sims/gacha-1pct-100.py      # out/gacha-1pct-100/ に mp4 ができる
python sims/gacha-1pct-100.py --stills   # 要所の静止画だけ
```

2026-09-28 以降の回はノートの見た目（`engine/note.py`）で、字は手書き風の [Klee One](https://fonts.google.com/specimen/Klee+One)（SIL Open Font License、`fonts/` に同梱）を使います。
Windows なら `fonts/KleeOne-SemiBold.ttf` をダブルクリックしてインストールしてください。それより前の回の字はメイリオです。

## 答えの確かめ方

- 各ファイルは、シミュレーションの結果と理論値（数式）を照合し、ずれていたら動画を書き出しません（`check_answers`）。
- 乱数の種は、最初に見せる「1人目」「1部屋目」の見本が分かりやすくなるように選んでいます。
  答えの数字は、全試行（1万回など）の結果から計算しています。

## 動画の一覧

| 公開日 | 問い | 動画 | コード |
|---|---|---|---|
| 2026-10-20 | 渋滞で車線を変える車は、早く着く？（片側2車線・5km） | [見る](https://youtube.com/shorts/eCsPgwDnBZ0) | [`shasen-henkou.py`](sims/shasen-henkou.py) |
| 2026-10-19 | レジ、カゴが軽い列と人が少ない列、どっちが早い？（5人×8点 と 2人×20点） | [見る](https://youtube.com/shorts/CDIkJ-6qvmc) | [`reji-ninzu.py`](sims/reji-ninzu.py) |
| 2026-10-18 | 30分の外出、エアコン暖房はつけっぱなしと消す、どっちが安い？ | [見る](https://youtube.com/shorts/ihynyMrzOHY) | [`aircon-tsukeppanashi.py`](sims/aircon-tsukeppanashi.py) |
| 2026-10-17 | 1万人と5千人が弓で撃ち合う（腕前は同じ）。勝った側は何人残る？ 腕前・刀・狭い道・分けて戦うと？（ランチェスターの法則） | [見る](https://youtube.com/shorts/J8JWkF_Oqy0) | [`kassen-long.py`](sims/kassen-long.py) |
| 2026-10-17 | コーヒーにミルク、先に入れると冷めにくい？（10分待って飲む） | [見る](https://youtube.com/shorts/JIykP3wSRb4) | [`coffee-milk.py`](sims/coffee-milk.py) |
| 2026-10-16 | シャッフル再生で、同じ歌手が続く。これって偏ってる？（50曲・歌手10人×5曲・最初の20曲） | [見る](https://youtube.com/shorts/O8pJKZa-jXY) | [`shuffle-saisei.py`](sims/shuffle-saisei.py) |
| 2026-10-15 | 車を飛ばしても、次の信号で追いつかれる？（制限60kmの道を40kmと60kmで・信号8つ） | [見る](https://youtube.com/shorts/QHQ_ZVBvweA) | [`shingou-tobasu.py`](sims/shingou-tobasu.py) |
| 2026-10-14 | 雪の結晶、同じ形はある？（1万個を、それぞれの空で育てて比べる） | [見る](https://youtube.com/shorts/Sbo3M0J3NpA) | [`yuki-kesshou.py`](sims/yuki-kesshou.py) |
| 2026-10-13 | 砂時計、砂が減ると速く落ちているように感じる？（砂1万粒の砂時計と水時計） | [見る](https://youtube.com/shorts/AndQs7BFbVc) | [`sand-dokei.py`](sims/sand-dokei.py) |
| 2026-10-12 | 傘をさして雨の中を100m。歩くのと走るの、どちらが濡れない？ 傘を前に出して傾けたら・傘の大きさ・追い風/向かい風だと？ | [見る](https://youtube.com/shorts/LeThiF7pdlo) | [`ame-long.py`](sims/ame-long.py) |
| 2026-10-12 | バターの面が下になるのは、気のせい？（トーストをそっと落とす。1万枚） | [見る](https://youtube.com/shorts/deJjeL0e3Gs) | [`toast-butter.py`](sims/toast-butter.py) |
| 2026-10-11 | エスカレーター、片側あける？2列で立つ？ 100人の平均、早いのは？ | [見る](https://youtube.com/shorts/PSDqj-H7EZk) | [`escalator-2retsu.py`](sims/escalator-2retsu.py) |
| 2026-10-10 | 平均10分おきのバスで、なぜ10分も待つのか（待ち時間のパラドックス・団子運転・時間調整） | [見る](https://youtube.com/shorts/5qwx23CGRuE) | [`bus-matsu-long.py`](sims/bus-matsu-long.py) |
| 2026-10-10 | 100人と50人が弓で撃ち合う（腕前は同じ）。勝った側は何人残る？ | [見る](https://youtube.com/shorts/Kr6BaklYUO0) | [`kassen-2bai.py`](sims/kassen-2bai.py) |
| 2026-10-09 | 雨の中、傘なしで100m。走ると濡れない？ | [見る](https://youtube.com/shorts/WXgmO-lKFDk) | [`ame-hashiru.py`](sims/ame-hashiru.py) |
| 2026-10-08 | 高速の合流で1台がちょっとブレーキ。後ろで何台止まる？ | [見る](https://youtube.com/shorts/6lueki89zGg) | [`shizen-jutai.py`](sims/shizen-jutai.py) |
| 2026-10-07 | クラス35人。同じ誕生日の2人がいる確率は？ | [見る](https://youtube.com/shorts/gKtXC-N1510) | [`birthday-35nin.py`](sims/birthday-35nin.py) |
| 2026-10-06 | まずい店に行列ができる確率は？（100人が順に店を選ぶ。自分の舌は6割当たる） | [見る](https://youtube.com/shorts/dqIKEfCaVgY) | [`gyoretsu-mise.py`](sims/gyoretsu-mise.py) |
| 2026-10-05 | バスは平均10分おき（間隔はバラバラ）。バス停で平均何分待つ？ | [見る](https://youtube.com/shorts/FmiVQIw8UJw) | [`bus-matsu.py`](sims/bus-matsu.py) |
| 2026-10-04 | 1万人の町にゾンビ1体。1日1人かむ。全員ゾンビまで何日？ | [見る](https://youtube.com/shorts/kyIlnMHT57k) | [`zombie-10000.py`](sims/zombie-10000.py) |
| 2026-10-03 | 0.001度ずつずらした振り子1万本。10秒後どうなる？ | [見る](https://youtube.com/shorts/u72kZyE4qnw) | [`furiko-10000.py`](sims/furiko-10000.py) |
| 2026-10-02 | 表なら1.5倍、裏なら0.6倍を100回。得する人は何%？ | [見る](https://youtube.com/shorts/dVRuGlVY6rI) | [`bai-100kai.py`](sims/bai-100kai.py) |
| 2026-10-01 | コイン10回。表がちょうど5回になる確率は？ | [見る](https://youtube.com/shorts/dOFlvkgn_54) | [`coin-10kai.py`](sims/coin-10kai.py) |
| 2026-09-30 | 床の線に針を1万本落とす。線に重なるのは何本？ | [見る](https://youtube.com/shorts/RZDpqANNIcc) | [`hari-10000.py`](sims/hari-10000.py) |
| 2026-09-29 | 30人で席替え。誰も元の席に戻らない確率は？ | [見る](https://youtube.com/shorts/QqUfB-rXhus) | [`sekigae-30nin.py`](sims/sekigae-30nin.py) |
| 2026-09-28 | 10人でじゃんけん。あいこが終わるまで平均何回？ | [見る](https://youtube.com/shorts/m7eN1UpaNM0) | [`janken-10nin.py`](sims/janken-10nin.py) |
| 2026-09-27 | 全5種のおまけ。全部そろうまで平均何個？ | [見る](https://youtube.com/shorts/MCiG9GtCLEk) | [`omake-5shu-comp.py`](sims/omake-5shu-comp.py) |
| 2026-09-26 | 1%のガチャを100回。当たる人は何%？ | [見る](https://youtube.com/shorts/W4140l0DFmw) | [`gacha-1pct-100.py`](sims/gacha-1pct-100.py) |

## ライセンス

MIT License。授業や勉強会で自由に使ってください。
