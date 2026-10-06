# NewsGatherWeb

NHKニュースと時事通信の新着見出しを自動取得し、GitHub Pages上でWebサイトとして公開するツールです。

元のローカル版（`NewsGather`）をクラウド化したもので、GitHub Actions で定期的にニュース記事を取得し、静的HTMLサイトとして GitHub Pages で公開しています。

## アクセス

<https://Koichi51-Takahashi.github.io/NewsGatherWeb/>

（このリポジトリが公開設定で、GitHub Pages が有効になっていることが前提）

## 仕組み

1. 外部の定期実行サービス **cron-job.org** が、1日3回、決まった時刻に GitHub へ「実行してください」と指示を送り、**GitHub Actions** が起動する
2. NHKと時事通信の新着一覧ページを取得し、直近12時間以内の記事見出しを抽出
3. 記事本文（またはNHKの場合は要約文）を取得し、HTML形式で整形
4. 縦並び版（`index.html`）・横並び版（`report2.html`）の2種類を生成
5. `dist/` ディレクトリの内容が GitHub Pages として公開される

元の見た目・機能は保ったまま、クラウド上で自動化しました。

## ローカルでの実行方法（開発・テスト用）

初回セットアップ:

```powershell
cd C:\Users\TakahashiKoichi\Documents\project\NewsGatherWeb
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

実行:

```powershell
python main.py --quiet
```

`dist/index.html` が生成されます。ブラウザで `dist/index.html` を開いて見た目を確認できます。

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `main.py` | 実行の入り口。取得・解析・表示の流れを回す |
| `fetcher.py` | ページのHTMLを取得する |
| `parsers.py` | HTMLから見出し・時刻・リンクを抜き出す |
| `timeutil.py` | 時刻の解釈・12時間以内判定 |
| `config.py` | 取得対象のサイト一覧と設定 |
| `article.py` | 記事本文（またはNHKの場合は要約文）を取得 |
| `report.py` | 取得結果をHTML（`dist/index.html`・`dist/report2.html`）として書き出す |
| `.github/workflows/update-news.yml` | GitHub Actions のワークフロー定義（ニュース更新・公開） |
| `.github/workflows/check-docs.yml` | 文書チェックとlintを、pushのたびに実行するワークフロー |
| `check_docs.py` | このプロジェクト独自の文書の決まりを確認する（必須見出し・リンク切れ・古い記述・設定との食い違い） |
| `requirements-dev.txt` | lint用の道具の一覧（本番の更新には使わない） |
| `pyproject.toml` | lint（ruff・pymarkdown）の設定 |
| `.yamllint` | lint（yamllint）の設定 |

## キャッシュについて

ローカル版（`NewsGather`）は記事本文をローカルに48時間キャッシュしていました。

GitHub Pages版では **キャッシュなし** で毎回すべての記事本文を新規取得しています。1回の実行で数十件程度の取得なので、実行時間は数秒〜十数秒で完了します。

## 定期実行（GitHub Actions）

GitHub Actions 内蔵の定期実行機能（`schedule`）は実測で1〜2.7時間遅れたため廃止し、外部の定期実行サービス **cron-job.org** から GitHub の `workflow_dispatch`（実行を依頼する窓口）を呼び出す方式にしています。

- 実行する時刻・回数は cron-job.org 側のジョブ設定で管理しています（時刻は変更されることがあるため、この文書には書きません。最新の設定は cron-job.org を確認してください）
- cron-job.org が GitHub に使うアクセストークンには有効期限があります。失効前に再発行し、cron-job.org の3つのジョブの `Authorization` ヘッダーを更新してください
- `.github/workflows/update-news.yml` は `workflow_dispatch` のみを持ちます。GitHub の Actions タブから「Run workflow」を選ぶ手動実行もできます

## 文書チェックとlint

文書や設定の書き間違いで、ニュースの自動更新が止まったり、説明が実際の仕組みと食い違ったまま残ったりしないよう、2種類の自動点検を入れています。

- **文書チェック**（`check_docs.py`）：このプロジェクト独自の決まりを確認します。必須見出しがそろっているか、リンク先が実在するか、古い説明（例：GitHub内蔵の定期実行）が残っていないか、ワークフロー設定と文書が食い違っていないか。
- **lint（リント）**：世の中で標準的な書き方の決まりを、道具が自動で点検します。Pythonコードは `ruff`、ワークフローの設定ファイルは `yamllint`、Markdown文書は `pymarkdown` を使います。

違反があるとGitHub Actionsが失敗（赤）になります。文書チェックは、ニュース更新の実行のたび（取得の前）と、`push` のたびの両方で動きます。lintは `push` のときだけ動き、ニュース更新には影響しません。

手元で実行する場合（初回のみ `pip install -r requirements-dev.txt` が必要です）：

```powershell
python check_docs.py
ruff check .
yamllint .github
pymarkdown scan README.md docs/HOW_IT_WORKS.md
```

lintの決まりは、日本語の説明文に合わせて一部ゆるめています（理由は `pyproject.toml` と `.yamllint` のコメントを参照）。

## トラブルシューティング

### 時事通信の記事が取得できない場合

`fetcher.py` の `fetch_textise_html` が CloudFlare のボット対策でブロックされることがあります。

その場合は `config.py` の時事通信設定を `fetch: fetcher.fetch_direct_html` に変更し、textise.net経由をやめて直接取得に切り替えてください。

```python
{
    "name": "時事通信（新着）",
    "url": "https://www.jiji.com/sp/list?g=news",
    "parser": parsers.parse_jiji,
    "time_parser": timeutil.parse_jiji_time,
    "fetch": fetcher.fetch_direct_html,  # fetch_textise_html から変更
    "paginate": False,
    "article_fetcher": article.fetch_jiji_body,
    "article_is_summary": False,
},
```

### GitHub Pages のURL が間違っている場合

このリポジトリの **Settings** → **Pages** → **Build and deployment** を確認し、以下に設定してください:

- **Source**: GitHub Actions
- **Branch**: main

## 参考

- 元のローカル版: `C:\Users\TakahashiKoichi\Documents\project\NewsGather`
- GitHub Pages 公式: <https://pages.github.com/>
- GitHub Actions 公式: <https://github.com/features/actions>
