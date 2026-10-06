"""文書の決まりを機械的に確認するチェック処理。

README.md と docs/HOW_IT_WORKS.md が、このプロジェクトの決まりを守っているかを確認する。
違反が1件でもあれば、内容を「ファイル:行番号: 内容」の形で全て表示し、終了コード1で終わる
（GitHub Actionsではこれによりビルドが止まる）。

確認する決まり:
  R1 必須見出しがそろっているか
  R2 リンク先・ファイル名が実在するか
  R3 古い記述（現在の仕組みと食い違う表現）が残っていないか
  R4 ワークフロー設定と文書の説明が食い違っていないか

標準ライブラリだけで動くので、追加のインストールは不要。
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

README = "README.md"
HOW_IT_WORKS = "docs/HOW_IT_WORKS.md"
WORKFLOW = ".github/workflows/update-news.yml"

# 確認対象の文書（これ以外のmdファイルは対象外）
TARGET_DOCS = [README, HOW_IT_WORKS]

# R1: 文書ごとの必須見出し（「## 」で始まる行に、この文字列が含まれていること）
REQUIRED_HEADINGS = {
    HOW_IT_WORKS: [
        "この資料について",
        "全体像",
        "登場する用語の解説",
        "なぜこの仕組みが必要なのか",
        "処理の流れ",
        "ファイルの役割一覧",
        "実際に起きたトラブルの実例",
        "運用方法",
        "リスク・注意点",
        "参考リンク",
    ],
    README: [
        "仕組み",
        "ローカルでの実行方法",
        "ファイル構成",
        "定期実行",
    ],
}

# R3: 文書ごとの禁止表現（正規表現, 理由）。古くなった説明をここに足していく
STALE_PATTERNS = {
    README: [
        (r"GitHub Actions\*{0,2}\s*が毎日3回",
         "定期実行は外部のcron-job.orgが起動している。『GitHub Actionsが毎日3回』は古い説明"),
        (r"前日\s*23:45\s*UTC",
         "GitHub内蔵scheduleの時刻説明が残っている（現在は使っていない）"),
        (r"\d{1,2}:\d{2}\s*JST",
         "具体的な実行時刻は外部サービス側で変更されるため、READMEには書かない"),
    ],
    HOW_IT_WORKS: [
        (r"`schedule`を一時的に無効",
         "scheduleは廃止済み。停止方法はcron-job.org側のジョブ停止になった"),
    ],
}

errors = []


def report(path, line_no, message):
    errors.append(f"{path}:{line_no}: {message}")


def read_lines(rel_path):
    path = ROOT / rel_path
    if not path.exists():
        report(rel_path, 0, "ファイルが見つからない")
        return []
    return path.read_text(encoding="utf-8").splitlines()


def outside_code_blocks(lines):
    """コードブロック（```で囲まれた部分）の外の行だけを (行番号, 内容) で返す。"""
    in_block = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_block = not in_block
            continue
        if not in_block:
            yield number, line


def check_required_headings(rel_path, lines):
    headings = [line for _, line in outside_code_blocks(lines) if line.startswith("## ")]
    for required in REQUIRED_HEADINGS.get(rel_path, []):
        if not any(required in heading for heading in headings):
            report(rel_path, 1, f"必須見出しがない: 「{required}」")


LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def check_links(rel_path, lines):
    base = (ROOT / rel_path).parent
    for number, line in outside_code_blocks(lines):
        for target in LINK_PATTERN.findall(line):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            file_part = target.split("#")[0]
            if file_part and not (base / file_part).exists():
                report(rel_path, number, f"リンク切れ: {target}")


FILE_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def check_readme_file_table(lines):
    """READMEの「ファイル構成」表に書かれたファイル名が実在するか確認する。"""
    in_section = False
    for number, line in enumerate(lines, start=1):
        if line.startswith("## "):
            in_section = "ファイル構成" in line
            continue
        if not in_section:
            continue
        match = FILE_ROW_PATTERN.match(line)
        if match and not (ROOT / match.group(1)).exists():
            report(README, number, f"ファイル構成の表にあるファイルが存在しない: {match.group(1)}")


def check_stale_expressions(rel_path, lines):
    for pattern, reason in STALE_PATTERNS.get(rel_path, []):
        regex = re.compile(pattern)
        for number, line in outside_code_blocks(lines):
            if regex.search(line):
                report(rel_path, number, f"古い記述: {reason}")


def check_workflow_consistency(readme_lines):
    workflow_lines = read_lines(WORKFLOW)
    active = [(n, line) for n, line in enumerate(workflow_lines, start=1)
              if not line.lstrip().startswith("#")]
    for number, line in active:
        if re.match(r"^\s*schedule:", line):
            report(WORKFLOW, number,
                   "schedule:が有効になっている（定期実行は外部のcron-job.orgが担当する決まり）")
    if workflow_lines and not any(re.match(r"^\s*workflow_dispatch:", line) for _, line in active):
        report(WORKFLOW, 1, "workflow_dispatch:がない（cron-job.orgからの起動に必要）")
    if readme_lines and not any("cron-job.org" in line for line in readme_lines):
        report(README, 1, "READMEにcron-job.orgへの言及がない（定期実行の説明が現状と合っていない）")


def main():
    readme_lines = []
    for rel_path in TARGET_DOCS:
        lines = read_lines(rel_path)
        if rel_path == README:
            readme_lines = lines
        check_required_headings(rel_path, lines)
        check_links(rel_path, lines)
        check_stale_expressions(rel_path, lines)
    check_readme_file_table(readme_lines)
    check_workflow_consistency(readme_lines)

    if errors:
        print(f"文書チェック: {len(errors)}件の違反があります")
        for message in errors:
            print(f"  {message}")
        return 1
    print("文書チェック: 違反なし")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
