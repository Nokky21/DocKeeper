<div align="center">

# DocKeeper

**腐らないドキュメント。**

ドキュメントはコーディングエージェントが書きます。DocKeeper はすべての記述をその裏付けとなるコードに結び付け、そのコードが変わった瞬間に知らせます。

[![CI](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/Nokky21/DocKeeper/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-2ea44f)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](../../LICENSE)

[ウェブサイト](https://nokky21.github.io/DocKeeper/) · [ライブデモ](https://nokky21.github.io/DocKeeper/#demo) · [インストール](#install) · [リファレンス](../reference.md)

<sub>[English](../../README.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [Nederlands](README.nl.md) · [Polski](README.pl.md) · [Čeština](README.cs.md) · [Svenska](README.sv.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [Türkçe](README.tr.md) · [العربية](README.ar.md) · [עברית](README.he.md) · [हिन्दी](README.hi.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · **日本語** · [한국어](README.ko.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md) · [ไทย](README.th.md)</sub>

</div>

---

## なぜ必要か

今日書いた README は数か月後には間違っていて、どのページが嘘をついているのか誰にもわかりません。DocKeeper はこの「誰にもわからない」を、無料で、あなたのマシン上で解決します。

- **すべての記述がチェックされます。** 「支払いは請求前に検証される」という記述は、それを行う関数に結び付けられます。その関数が変わると、DocKeeper が知らせます。
- **チェックに AI は使いません。** 書くのはエージェント、チェックはフィンガープリントの比較なので、毎回同じ答えが返ります。
- **ローカルで無料。** アカウントもサーバーもネットワークも依存関係も不要。MIT ライセンス。

## 仕組み

<p align="center"><img src="../../site/public/assets/how-it-works.svg" alt="DocKeeper の仕組み: 記述をコードブロックにアンカーし、そのブロックのフィンガープリントを取り、check が OK、MOVED、CHANGED を報告する" width="100%"></p>

1. **アンカーする。** エージェントは各記述の横に、それがコードのどこにあるかを書きます: `[[src/payments.py#validate_payment]]`。ページをすっきりさせたいなら、同じものを HTML コメントの中に書きます。
2. **封印する。** `dockeeper scan` が各アンカーの裏にあるコード（たいていは関数全体）のフィンガープリントを取ります。整形し直しても影響はなく、ロジックを変えたときだけ反応します。
   <!-- dockeeper: dockeeper/bloques.py#bloque_en dockeeper/huellas.py#huella -->
3. **チェックする。** `dockeeper check` は記述ごとに判定を出します: `OK`、`MOVED`（コードが移動しただけで、`dockeeper fix` がレビューなしで追従します）、または `CHANGED`（コードが変わったので、人が読んで本文を更新します）。`CHANGED` がひとつでもあれば終了コードは 1 になり、CI は失敗します。
   <!-- dockeeper: dockeeper/motor.py#verificar_codigo dockeeper/motor.py#FALLOS -->

<p align="center"><img src="../../site/public/assets/terminal-check.svg" alt="コードを編集した後の dockeeper check の実際の出力: CHANGED が 1 件、MOVED が 1 件" width="100%"></p>

<a id="install"></a>

## インストール

`python3`（3.10 以降）と `git` が必要です。リポジトリを、名前がちょうど `dockeeper` のフォルダーにクローンしてください。

```bash
# Claude Code
git clone https://github.com/Nokky21/DocKeeper.git ~/.claude/skills/dockeeper

# Codex, Gemini CLI, Cursor, GitHub Copilot
git clone https://github.com/Nokky21/DocKeeper.git ~/.agents/skills/dockeeper
```

ほかのフォルダー、単一プロジェクト、Windows、claude.ai、API については[インストールガイド](../install.md)を参照してください。

## 使い方

エージェントに普段の言葉で頼みます。

- *「dockeeper でこのリポジトリのドキュメントを書いて。」* モノレポにも対応し、パッケージをひとつずつ進めます。
- *「ドキュメントがまだ正しいか確認して、正しくないところを直して。」*
- *「コミットのたびにドキュメントを見直して。」* コミットを決してブロックしない git フックをインストールします。
- *「git の履歴から意思決定のページを書いて。理由はでっち上げないで。」*

または、プロジェクトのルートで自分で実行します。

```bash
DK="python3 $HOME/.claude/skills/dockeeper/bin/dockeeper"
$DK audit    # 足りないもの: ページ、パッケージ、ドキュメントのないコード
$DK scan     # 新しいアンカーを封印し、それぞれが指すコードを表示
$DK check    # まだ正しい? 終了コード 0 = はい、1 = 何かが変わった
$DK fix      # 移動したコードに追従（封印ファイルだけを更新）
$DK review   # 直前のコミットがドキュメントにとって何を意味するか
```

<!-- dockeeper: dockeeper/motor.py#arreglar -->

## コミットのたびに

`review` は直前のコミット（`--desde main` ならブランチ全体）を調べ、影響を受けた記述、まだどの記述にも含まれていない新規または変更されたコード、そしてそれらのコミットにある、まだ書き残されていない意思決定を一覧にします。`post-commit` フックにしておけば、コミットした人（あなたでもエージェントでも）が毎回この一覧を目にし、ドキュメントがコードと一緒に育っていきます。
<!-- dockeeper: dockeeper/revision.py#revisar -->

```sh
#!/bin/sh
python3 "$HOME/.claude/skills/dockeeper/bin/dockeeper" review || true
```

## モノレポ

`audit` はすべてのパッケージ（`package.json`、`go.mod`、`Cargo.toml`、`pyproject.toml`、`pom.xml` などを含むサブフォルダー）を見つけ、ドキュメントのないものを示します。エージェントはまずルートのページをパッケージの地図付きで書き、そのあとパッケージをひとつずつ文書化するので、巨大なリポジトリでも収まります。 <!-- dockeeper: dockeeper/paquetes.py#detectar -->

## CI で

```yaml
- uses: actions/checkout@v6
- uses: Nokky21/DocKeeper@v0.2.0
```

ほかの CI でも必要なのは Python と git だけです: [クローンして `check` を実行](../reference.md#continuous-integration)。

## さらに詳しく

- [インストールガイド](../install.md): 各エージェント、単一プロジェクト、Windows、claude.ai、API。
- [リファレンス](../reference.md): アンカー、コマンド、判定、部分的な範囲、公開ドキュメント、「なぜ」、設定、制限、FAQ。
- エージェントが従う指示である [SKILL.md](../../SKILL.md) と[仕様書](../../SPEC.md)（どちらもスペイン語）。

## ライセンス

[MIT](../../LICENSE).

---

<sub>[英語の README](../../README.md) の翻訳です。内容が異なる場合は英語版が優先されます。インストールガイドとリファレンスは英語です。</sub>
