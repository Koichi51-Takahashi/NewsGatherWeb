# テスト仕様書兼成績書：文書チェック（check_docs.py）とlint

## 1. 概要

| 項目 | 内容 |
|---|---|
| 対象 | NewsGatherWebへ追加した「文書チェック（`check_docs.py`）」と「lint（ruff・yamllint・pymarkdown）」、およびGitHub Actionsへの組み込み |
| 実施日 | 2026-10-06 |
| 目的 | 文書や設定の書き間違いを機械が見つけ、違反時に失敗（赤）になること。かつ、既存のニュース更新（取得→HTML生成→公開）を壊さないこと |
| 総合判定 | 実施した全テストが合格。未実施の項目が3件あり（9章に理由を記載） |
| 更新履歴 | 2026-10-06 午前：初版。同日午後：D-7（自動実行）を実施し、E-1を完了 |

## 2. テスト環境

| 区分 | 内容 |
|---|---|
| ローカル | Windows 11 Pro、Python 3.11（venv）、ruff 0.16.10、yamllint 1.38.0、pymarkdownlnt 0.9.40 |
| GitHub Actions | ubuntu-latest、Python 3.12（lint道具は`requirements-dev.txt`の最新版） |
| リポジトリ | `Koichi51-Takahashi/NewsGatherWeb`（公開） |
| 時刻の表記 | 本書は日本時間（JST）。GitHubの実行記録はUTCのため、9時間を足して読み替えた |

## 3. テストの方針

- 各点検について、①**正常系**（違反が無ければ成功する）と、②**異常系**（わざと決まりを破ると、失敗して場所が分かる）の両方を確認する
- わざと破るテストは、**ローカルの退避コピー付き**と**テスト用ブランチ**でのみ行い、`main`には破った状態を置かない（本番の自動更新を止めないため）
- 判定は「合格」「未実施」の2種類

## 4. テスト項目と結果：文書チェック（`check_docs.py`、ローカル）

| ID | 目的 | 手順 | 期待結果 | 実測結果 | 判定 |
|---|---|---|---|---|---|
| A-1 | 既存の食い違いを検出できる（異常系） | README修正前に`python check_docs.py`を実行 | 違反が検出され終了コード1 | 7件検出、終了コード1（README.md:15・65・66・67の「毎日3回」「前日 23:45 UTC」「具体的な時刻」、cron-job.orgへの言及なし） | 合格 |
| A-2 | 正しい文書では成功する（正常系） | READMEを現状（cron-job.org方式）に修正して再実行 | 違反なし、終了コード0 | 「文書チェック: 違反なし」、終了コード0 | 合格 |
| A-3 | 必須見出しの欠落を検出（R1） | HOW_IT_WORKS.mdの見出し「8. 運用方法」を「8. 使い方」に一時変更 | 違反1件、終了コード1 | `docs/HOW_IT_WORKS.md:1: 必須見出しがない: 「運用方法」`、終了コード1 | 合格 |
| A-4 | リンク切れを検出（R2） | READMEに存在しないファイルへのリンク`[存在しない資料](docs/NOT_EXIST.md)`を一時追記 | 違反1件、終了コード1 | `README.md:103: リンク切れ: docs/NOT_EXIST.md`、終了コード1 | 合格 |
| A-5 | 古い記述を検出（R3） | READMEに「GitHub Actions が毎日3回自動実行されます。」を一時追記 | 違反1件、終了コード1 | `README.md:103: 古い記述: 定期実行は外部のcron-job.orgが起動している…`、終了コード1 | 合格 |
| A-6 | 破ったものを元に戻すと成功に戻る | A-3〜A-5の変更を退避コピーから復元して再実行 | 違反なし、終了コード0。HOW_IT_WORKS.mdに差分なし | 違反なし、終了コード0。`git status`でHOW_IT_WORKS.mdは未変更、READMEは意図した修正のみ | 合格 |

## 5. テスト項目と結果：lint（ローカル）

### 5.1 導入と設定調整

| ID | 目的 | 手順 | 期待結果 | 実測結果 | 判定 |
|---|---|---|---|---|---|
| B-1 | 道具が導入できる | `pip install -r requirements-dev.txt` | 3つの道具が入る | 初回は失敗（`requirements-dev.txt`の日本語コメントをWindowsのpipが文字コード cp932 で読めず）。コメントを半角英数字に変更して再実行し、ruff 0.16.10・yamllint 1.38.0・pymarkdownlnt 0.9.40が導入された | 合格（不具合を1件修正） |
| B-2 | 標準設定での指摘を把握する | 設定ファイルを置く前の状態で3つの道具を実行 | 指摘が出る | ruff 4件（BLE001が3件、I001が1件）、yamllint警告2件（document-start、truthy）、pymarkdownは行の長さ（MD013）を中心に多数（出力は先頭40行で切り詰め） | 合格 |
| B-3 | 設定が効く | `pyproject.toml`・`.yamllint`を作成して再実行 | 日本語の長い行・重複見出し・YAMLの`on:`の指摘が消える | yamllintは指摘0件。pymarkdownはMD013・MD024が消え、残りはMD034（URL裸書き）3件とMD036（強調の見出し代用）1件。pymarkdownが`pyproject.toml`を自動で読み込むことも確認 | 合格 |
| B-4 | 残る指摘を全て直すと全て成功 | MD034・MD036を文書側で修正、ruffの`import`順を`--fix`で修正、`except Exception`3箇所に理由付き`# noqa`を追記 | 全ての点検が成功 | `ruff check` All checks passed、`yamllint`終了コード0、`pymarkdown scan`終了コード0、`check_docs.py`違反なし | 合格 |

### 5.2 わざと破る（異常系）

| ID | 目的 | 手順 | 期待結果 | 実測結果 | 判定 |
|---|---|---|---|---|---|
| B-5 | ruffが失敗する | `article.py`の先頭に使わない`import os`を一時追加 | 指摘が出て終了コード1 | 5件（F401 未使用import、I001 並び順、E402 ×3）、終了コード1 | 合格 |
| B-6 | yamllintが失敗する | `check-docs.yml`の`runs-on`の字下げを一時的に崩す | 指摘が出て終了コード1 | 2件（indentation、syntax error）、終了コード1 | 合格 |
| B-7 | pymarkdownが失敗する | READMEに見出しレベルを飛ばした`####`を一時追記 | 指摘が出て終了コード1 | 3件（MD001 見出しレベル、MD022、MD012）、終了コード1 | 合格 |
| B-8 | 元に戻すと全て成功に戻る | 退避コピーから3ファイルを復元し、全点検を再実行 | 全て成功 | 文書チェック違反なし、ruff All checks passed、yamllint・pymarkdown 終了コード0 | 合格 |

## 6. テスト項目と結果：既存動作への影響（ローカル）

| ID | 目的 | 手順 | 期待結果 | 実測結果 | 判定 |
|---|---|---|---|---|---|
| C-1 | コード修正が動作を壊していない | `article.py`・`main.py`修正後に`python main.py --quiet`を実行 | エラーなく終了し、`dist/index.html`・`dist/report2.html`が生成される | 終了コード0、2ファイルが更新された。コードの差分は`import`の並び順とコメント追記のみ（`git diff --stat`で2ファイル・各数行） | 合格 |

## 7. テスト項目と結果：GitHub Actions

| ID | 目的 | 手順 | 期待結果 | 実測結果 | 判定 |
|---|---|---|---|---|---|
| D-1 | pushで文書チェックとlintが動き、正しい版は成功する | テスト用ブランチ`test/check-docs`へpush（9:15） | `Check Docs`が起動し成功 | run 37393049611：success。文書チェック・ruff・yamllint・pymarkdownの全ステップが success | 合格 |
| D-2 | 違反版は失敗（赤）になる | 同ブランチへ、READMEに古い記述を足したコミットをpush（9:16） | 文書チェックのステップで失敗し、後続は実行されない | run 37393113184：failure。「Check docs (project rules)」が failure、ruff・yamllint・pymarkdownは skipped | 合格 |
| D-3 | 違反コミットを`main`へ入れない | 違反を含まない正しいコミットのみを`main`へ早送りで反映し、テスト用ブランチを削除 | `main`のREADMEに違反表現が無い。ブランチがリモート・ローカルから消える | 違反表現は0件、`check_docs.py`違反なし。ブランチ一覧は`main`のみ | 合格 |
| D-4 | `main`でも成功する | `main`へpush（9:17） | `Check Docs`が成功 | run 37393191823：success | 合格 |
| D-5 | 本番の更新ジョブに追加したチェックが組み込まれ、既存動作を壊さない | `Update News`を手動実行（`workflow_dispatch`、9:19） | Check docs→取得→HTML生成→Pages公開が全て成功 | run 37393356853：success。「Check docs」「Fetch news and generate HTML」「Upload Pages artifact」「Deploy to GitHub Pages」が全て success | 合格 |
| D-6 | 公開しない文書をコミットしていない | コミット前に`git diff --cached`と`git status`を確認 | ステージは意図した10ファイルのみ | 10ファイル（新規6・変更4）のみ。伝達事項のmd、`temp/`、会話エクスポートのtxtなど未追跡4件はコミットされず | 合格 |
| D-7 | cron-job.orgの自動実行が、追加した「Check docs」込みで成功する | 11:57 JSTの定刻の自動実行（cron-job.org経由の`workflow_dispatch`）を、発火後に実行履歴で確認 | 定刻から数秒以内に開始し、Check docs→取得→公開が全て成功 | run 37406632159：success、開始 2:57:03 UTC（＝11:57:03 JST、定刻から3秒）。「Check docs」「Fetch news and generate HTML」「Upload Pages artifact」「Deploy to GitHub Pages」が全て success | 合格 |

## 8. テスト中に見つかった不具合・課題

| No. | 内容 | 対応 | 状態 |
|---|---|---|---|
| 1 | READMEに、実際の仕組みと食い違う古い説明が残っていた（「GitHub Actionsが毎日3回自動実行」、前日23:45 UTCなど）。A-1で検出 | READMEを現状（cron-job.org方式）に修正。具体的な時刻は文書に書かない決まりとした | 解決済み |
| 2 | `requirements-dev.txt`に日本語コメントがあると、Windowsのpipが文字コードで失敗した（B-1） | コメントを半角英数字に変更 | 解決済み |
| 3 | `except Exception`（ruffのBLE001）が3件指摘された | 「1つの失敗で全体を止めない」意図した書き方のため、理由付きの`# noqa`で例外扱いにした | 解決済み |
| 4 | HOW_IT_WORKS.mdにも、固定の実行時刻（8:45・11:57・17:45）という古い記述があった | 「cron-job.orgのジョブ設定で決まり、変更されることがある」に修正 | 解決済み |

## 9. 未実施の項目（正直な記録）

| ID | 内容 | 未実施の理由 | 今後の扱い |
|---|---|---|---|
| E-2 | `check_docs.py`の一部ルールの異常系：R4（`schedule:`が有効になっている／`workflow_dispatch:`が無い）、R2のファイル構成表の実在確認、HOW_IT_WORKS.md側の禁止表現 | 今回は代表例（A-3〜A-5）に絞ったため。正常系（違反なし）は通っている | 次回、ルールを追加・変更する際に併せて確認する |
| E-3 | 本番の`Update News`の中でチェックが失敗したとき、ニュース更新が止まること | 本番の自動更新を止めかねないため、`main`・本番では破らない方針。止まる仕組み自体は、同じスクリプトの終了コード1でD-2のとおり動作確認済み | 必要になれば、テスト用ブランチでワークフローを複製して確認する |
| E-4 | コード修正前後で、生成されるHTMLの内容が完全に同一であること | 取得するニュースが時間で変わるため、内容の完全一致は比較できない。C-1では正常終了と生成のみ確認 | 差分が`import`順とコメントのみであることをもって代替 |

## 10. 結論

- 文書チェックとlintは、正常系・異常系とも想定どおり動作した（A-1〜A-6、B-1〜B-8、C-1、D-1〜D-6）
- 違反は「ファイル:行番号」つきで表示され、GitHub Actions上でも赤（失敗）になる
- 本番のニュース更新は、追加後も手動実行で成功しており、`main`に違反は混入していない
- 定刻の自動実行（cron-job.org経由）も、追加ステップ込みで成功した（D-7）
- 未実施項目は9章のE-2〜E-4の3件（理由と今後の扱いを記載）
