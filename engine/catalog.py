"""catalog.json（公開済みの動画の一覧）から README.md を作り直す。

動画を1本公開するたびに catalog.json に1行足して、これを実行する。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/hollowmark-dev/medetashikame"

HEAD = """# めでたしかめ

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
"""

TAIL = """
## ライセンス

MIT License。授業や勉強会で自由に使ってください。
"""


def build():
    cat = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    rows = cat.get("videos", [])
    lines = [HEAD]
    if not rows:
        lines.append("\n（準備中）\n")
    else:
        lines.append("| 公開日 | 問い | 動画 | コード |")
        lines.append("|---|---|---|---|")
        for v in sorted(rows, key=lambda v: v["date"], reverse=True):
            lines.append(f"| {v['date']} | {v['question']} | [見る](https://youtube.com/shorts/{v['youtube_id']}) "
                         f"| [`{v['slug']}.py`](sims/{v['slug']}.py) |")
    lines.append(TAIL)
    # 改行は LF にそろえる（Windows で書くと CRLF になり、クラウドのルーティンが書くたびに全体が差分になる）
    with open(ROOT / "README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def code_url(slug):
    """概要欄に貼る、その回のコードへの直リンク"""
    return f"{REPO}/blob/main/sims/{slug}.py"


if __name__ == "__main__":
    build()
    print("README.md を更新しました")
