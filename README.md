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
| 2026-11-12 | 1,000の名字は、何年で1つになる？ | [見る](https://youtube.com/shorts/wQzjJ12UYIU) | [`myoji-kieru.py`](sims/myoji-kieru.py) |
| 2026-11-12 | 江戸の夜、提灯なしで月明かりだけで家に帰れる？（1万人・夜と天気は江戸の日記からくじ。最悪・最良・中央値／満月の夜なら／冬と夏） | [見る](https://youtube.com/shorts/rt1W9xHgo7E) | [`yomichi-long.py`](sims/yomichi-long.py) |
| 2026-11-11 | サメに襲われたら、イワシの群れの真ん中は安全？ | [見る](https://youtube.com/shorts/Ti0Lk1kqUVA) | [`iwashi-mure.py`](sims/iwashi-mure.py) |
| 2026-11-10 | 一斉にじゃんけん、1回で決まりやすいのは何人まで？ | [見る](https://youtube.com/shorts/aiYirzi2wjc) | [`janken-issei.py`](sims/janken-issei.py) |
| 2026-11-10 | もしあなたがツバメのヒナに生まれたら、何日生きられる？（卵1万個・1万回。日本・イギリス・スイスの記録をつないだツバメ） | [見る](https://youtube.com/shorts/5ahi4tLbpwQ) | [`tsubame-long.py`](sims/tsubame-long.py) |
| 2026-11-09 | 冬の夕焼けが赤いと言われるのは、空気が澄んでいるから？太陽が低いから？ | [見る](https://youtube.com/shorts/LaaAO6qcXh4) | [`yuuyake-akai.py`](sims/yuuyake-akai.py) |
| 2026-11-08 | お湯と水、冷凍庫で先に凍るのは？ | [見る](https://youtube.com/shorts/pSZbPnmK8Mg) | [`oyu-mizu-touketsu.py`](sims/oyu-mizu-touketsu.py) |
| 2026-11-07 | 宇宙人に出会える確率は？（ドレイクの式の決まっていない数を、2018年の論文と同じ幅から1万回選ぶ。「いる」と「出会える」の差） | [見る](https://youtube.com/shorts/-gCy09ouaSg) | [`uchujin-long.py`](sims/uchujin-long.py) |
| 2026-11-07 | 加湿器、床に置く？高い所に置く？ | [見る](https://youtube.com/shorts/Pf9hVo3qq4E) | [`kashitsuki-basho.py`](sims/kashitsuki-basho.py) |
| 2026-11-06 | おにぎり、アルミホイルとラップ、冷めにくいのは？ | [見る](https://youtube.com/shorts/WyXjH45Ntkk) | [`onigiri-tsutsumi.py`](sims/onigiri-tsutsumi.py) |
| 2026-11-05 | 長篠の戦い、鉄砲の三段撃ちは本当に強かった？（鉄砲の数・撃ち方・馬を下りる・柵・当たりやすさを変えて、柵を越えるまでに止められた人数を見る） | [見る](https://youtube.com/shorts/xEq_06g1ODc) | [`nagashino-long.py`](sims/nagashino-long.py) |
| 2026-11-05 | 冬の外で、スマホの電池が急に減るのは、寒さ？使いすぎ？ | [見る](https://youtube.com/shorts/qrisEIY2GFQ) | [`sumaho-samusa.py`](sims/sumaho-samusa.py) |
| 2026-11-04 | マグカップと湯のみ、冷めにくいのは？ | [見る](https://youtube.com/shorts/Eq1KeJuzSEk) | [`magu-yunomi.py`](sims/magu-yunomi.py) |
| 2026-11-03 | 満員電車で座っている人の前に立つとき、どこに立てば・どの駅で座れる？（例えば中央線の朝の上り。公表の数字をもとにした模型） | [見る](https://youtube.com/shorts/KRhY8bzN0xg) | [`densha-long.py`](sims/densha-long.py) |
| 2026-11-03 | カーテンを閉めると、窓の結露は増える？減る？ | [見る](https://youtube.com/shorts/3BtEacNSd6w) | [`kaaten-ketsuro.py`](sims/kaaten-ketsuro.py) |
| 2026-11-02 | シャボン玉が長く割れないのは、冬？夏？ | [見る](https://youtube.com/shorts/BLLTzLuPxEs) | [`shabon-kisetsu.py`](sims/shabon-kisetsu.py) |
| 2026-11-01 | 電車の窓が曇るのは、外が寒いから？人が多いから？ | [見る](https://youtube.com/shorts/2lvaAz4uXkM) | [`densha-kumori.py`](sims/densha-kumori.py) |
| 2026-10-31 | やかんの湯気、白く見えるのは口のすぐそば？少し離れたところ？ | [見る](https://youtube.com/shorts/x3p5WkJJMGM) | [`yakan-yuge.py`](sims/yakan-yuge.py) |
| 2026-10-31 | 桶狭間をもう一度戦ったら、2千人の織田は2万5千人の今川に勝てる？（条件をひとつずつ足して勝率を見る） | [見る](https://youtube.com/shorts/TclMzmEREkc) | [`okehazama-long.py`](sims/okehazama-long.py) |
| 2026-10-30 | 冬、遠くの電車の音がよく聞こえるのは、昼？夜？ | [見る](https://youtube.com/shorts/KtJV2fgaVfk) | [`yoru-oto.py`](sims/yoru-oto.py) |
| 2026-10-29 | 寒い朝、エアコン暖房の風向きは上？下？足もとが早く暖まるのは？ | [見る](https://youtube.com/shorts/I9mjuVtb9uI) | [`aircon-kazamuki.py`](sims/aircon-kazamuki.py) |
| 2026-10-29 | 2200年前のエラトステネスは、棒1本と影で地球の大きさを当てた？（棒を長く・距離をきちんと・何日も平均・影の先をくっきり・町が近かったら・本人の答えは当たっていた？） | [見る](https://youtube.com/shorts/l7HKJpa1SLU) | [`chikyu-long.py`](sims/chikyu-long.py) |
| 2026-10-28 | 寒い朝、洗濯物は外干しと部屋干し、どっちが早く乾く？ | [見る](https://youtube.com/shorts/Dw6vmJiusWI) | [`sentaku-hoshi.py`](sims/sentaku-hoshi.py) |
| 2026-10-27 | エレベーターを待つか、階段で行くか。何階までなら階段が早い？（3階・逆転する階・表示を見てから決める・朝の混雑・下り） | [見る](https://youtube.com/shorts/r5QoJI6xmEU) | [`kaidan-long.py`](sims/kaidan-long.py) |
| 2026-10-27 | お風呂上がり、タオルで拭いてからドライヤー？すぐドライヤー？どっちが早く乾く？ | [見る](https://youtube.com/shorts/XwEmkpOQpP8) | [`dryer-towel.py`](sims/dryer-towel.py) |
| 2026-10-26 | 駅の改札、空いている端と人の多い真ん中、どっちが早い？ | [見る](https://youtube.com/shorts/RP8V356WreM) | [`kaisatsu-hashi.py`](sims/kaisatsu-hashi.py) |
| 2026-10-25 | 冷える夜、毛布は羽毛布団の上？下？ | [見る](https://youtube.com/shorts/151jhIgaAQI) | [`moufu-kasane.py`](sims/moufu-kasane.py) |
| 2026-10-24 | お湯500mL、やかん（ガス・強火）と電気ケトル、どっちが早く沸く？ | [見る](https://youtube.com/shorts/sPQZc6wt7RI) | [`yakan-kettle.py`](sims/yakan-kettle.py) |
| 2026-10-24 | 伊能忠敬のように歩いて測った日本地図は、測り方の工夫を足すとどこまで正確になる？（1800年の第1次測量の道すじ・1万回） | [見る](https://youtube.com/shorts/U2sVcZdJ0rM) | [`inoh-long.py`](sims/inoh-long.py) |
| 2026-10-23 | 焼き芋、レンジとじっくり焼く、どっちが甘い？ | [見る](https://youtube.com/shorts/wxKbiD0QjXw) | [`yakiimo-amasa.py`](sims/yakiimo-amasa.py) |
| 2026-10-22 | 階段とエレベーター、3階までどっちが早い？ | [見る](https://youtube.com/shorts/QK46V-ceLos) | [`kaidan-elevator.py`](sims/kaidan-elevator.py) |
| 2026-10-21 | エスカレーターの片側あけが2列で立つより早くなるのは、歩く人が何割のとき？（電車1本・朝の混雑・ゆっくり歩く人・長いエスカレーター・横に階段） | [見る](https://youtube.com/shorts/uObC0AazxKY) | [`escalator-long.py`](sims/escalator-long.py) |
| 2026-10-21 | 持久走、最初に飛ばす？同じペースで走る？（同じ力の2人・1,500m） | [見る](https://youtube.com/shorts/5FRq6Np83oM) | [`jikyusou-pace.py`](sims/jikyusou-pace.py) |
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
