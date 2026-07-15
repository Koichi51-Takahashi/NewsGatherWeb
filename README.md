# NewsGatherWeb

NHKニュースと時事通信の新着見出しを自動取得し、GitHub Pages上でWebサイトとして公開するツールです。

元のローカル版（`NewsGather`）をクラウド化したもので、GitHub Actions で定期的にニュース記事を取得し、静的HTMLサイトとして GitHub Pages で公開しています。

## アクセス

https://{ユーザー名}.github.io/NewsGatherWeb/

（このリポジトリが公開設定で、GitHub Pages が有効になっていることが前提）

## 仕組み

1. **GitHub Actions** が毎日3回（8:45・11:57・17:45 JST）自動実行される
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
|---|---|
| `main.py` | 実行の入り口。取得・解析・表示の流れを回す |
| `fetcher.py` | ページのHTMLを取得する |
| `parsers.py` | HTMLから見出し・時刻・リンクを抜き出す |
| `timeutil.py` | 時刻の解釈・12時間以内判定 |
| `config.py` | 取得対象のサイト一覧と設定 |
| `article.py` | 記事本文（またはNHKの場合は要約文）を取得 |
| `report.py` | 取得結果をHTML（`dist/index.html`・`dist/report2.html`）として書き出す |
| `.github/workflows/update-news.yml` | GitHub Actions のワークフロー定義 |

## キャッシュについて

ローカル版（`NewsGather`）は記事本文をローカルに48時間キャッシュしていました。

GitHub Pages版では **キャッシュなし** で毎回すべての記事本文を新規取得しています。1回の実行で数十件程度の取得なので、実行時間は数秒〜十数秒で完了します。

## 定期実行（GitHub Actions）

`.github/workflows/update-news.yml` で以下のタイミングで自動実行されます:

- **8:45 JST**（前日 23:45 UTC）
- **11:57 JST**（2:57 UTC）
- **17:45 JST**（8:45 UTC）

また `workflow_dispatch` で手動実行も可能です（GitHub の Actions タブから「Run workflow」を選択）。

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
- GitHub Pages 公式: https://pages.github.com/
- GitHub Actions 公式: https://github.com/features/actions
