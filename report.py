"""取得結果をHTMLファイルとして書き出す処理。Webブラウザで見やすく表示するためのもの。

縦に並べる通常版（index.html）と、NHK・時事通信を左右に並べる横並び版
（report2.html）の2種類を作る。どちらで読むかはコーイチさんが選べるよう、
互いへのリンクを付けている。

GitHub Pages版では毎回すべての記事本文を取得し直す（キャッシュなし）。
"""

import hashlib
import html as html_lib
from datetime import datetime
from pathlib import Path

_OUTPUT_DIR = Path(__file__).parent / "dist"
_OUTPUT_PATH = _OUTPUT_DIR / "index.html"
_OUTPUT_PATH_2COL = _OUTPUT_DIR / "report2.html"
_ARTICLES_DIR = _OUTPUT_DIR / "articles"

_STYLE = """
  body { font-family: "Meiryo", "Yu Gothic", sans-serif; max-width: 720px; margin: 2em auto; padding: 0 1em; color: #222; background: #fafafa; }
  h1 { font-size: 1.3em; }
  h2 { border-bottom: 2px solid #444; padding-bottom: 0.3em; margin-top: 2em; }
  .updated { color: #666; font-size: 0.9em; }
  .switch { font-size: 0.9em; }
  .article { margin: 1em 0; padding: 0.8em 1em; background: #fff; border: 1px solid #ddd; border-radius: 6px; }
  .time { color: #666; font-size: 0.9em; }
  .title { font-weight: bold; margin: 0.2em 0 0.6em; }
  .links a { margin-right: 1.2em; text-decoration: none; color: #1a5fb4; }
  .links a:hover { text-decoration: underline; }
  .empty, .error { color: #888; font-style: italic; }
"""

_STYLE_2COL = """
  body { font-family: "Meiryo", "Yu Gothic", sans-serif; max-width: 1400px; margin: 2em auto; padding: 0 1em; color: #222; background: #fafafa; }
  h1 { font-size: 1.3em; }
  h2 { border-bottom: 2px solid #444; padding-bottom: 0.3em; margin-top: 0; }
  .updated { color: #666; font-size: 0.9em; }
  .switch { font-size: 0.9em; }
  .columns { display: flex; gap: 1.5em; align-items: flex-start; }
  .column { flex: 1 1 0; min-width: 0; }
  .article { margin: 1em 0; padding: 0.8em 1em; background: #fff; border: 1px solid #ddd; border-radius: 6px; }
  .time { color: #666; font-size: 0.9em; }
  .title { font-weight: bold; margin: 0.2em 0 0.6em; }
  .links a { margin-right: 1.2em; text-decoration: none; color: #1a5fb4; }
  .links a:hover { text-decoration: underline; }
  .empty, .error { color: #888; font-style: italic; }
  @media (max-width: 900px) {
    .columns { flex-direction: column; }
  }
"""

_ARTICLE_STYLE = """
  body { font-family: "Meiryo", "Yu Gothic", sans-serif; max-width: 640px; margin: 2em auto; padding: 0 1em; color: #222; background: #fafafa; line-height: 1.8; }
  .back { display: block; margin-bottom: 0.3em; }
  .time { color: #666; font-size: 0.9em; }
  .note { color: #888; font-style: italic; }
  .original { margin-top: 2em; }
"""


def _article_filename(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]
    return f"{digest}.html"


def _build_article_page(item: dict, body_text: str, is_summary: bool) -> str:
    title = html_lib.escape(item["title"])
    time_label = html_lib.escape(item["time"] or "時刻不明")
    original_url = html_lib.escape(item["url"])
    note = (
        '<p class="note">（この記事は要約文までしか公開されておらず、全文はありません）</p>'
        if is_summary else ""
    )
    body_html = "".join(
        f"<p>{html_lib.escape(paragraph)}</p>" for paragraph in body_text.split("\n\n")
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{_ARTICLE_STYLE}</style>
</head>
<body>
<a class="back" href="../index.html">← 一覧に戻る（縦並び）</a>
<a class="back" href="../report2.html">← 一覧に戻る（横並び）</a>
<h1>{title}</h1>
<p class="time">{time_label}</p>
{note}
{body_html}
<p class="original"><a href="{original_url}" target="_blank" rel="noopener">元の記事を開く</a></p>
</body>
</html>
"""


def _save_article(item: dict, article_fetcher, is_summary: bool) -> str | None:
    """記事本文（または要約）を取得し、HTMLファイルとして保存する。毎回新規取得。

    取得できなかった場合はNoneを返す（呼び出し側でリンクを省略する）。
    """
    filename = _article_filename(item["url"])
    filepath = _ARTICLES_DIR / filename

    body_text = article_fetcher(item["url"])
    if not body_text:
        return None

    _ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(_build_article_page(item, body_text, is_summary), encoding="utf-8")
    return f"articles/{filename}"


def _build_article_div(item: dict, article_fetcher, is_summary: bool) -> str:
    time_label = html_lib.escape(item["time"] or "時刻不明")
    title = html_lib.escape(item["title"])
    original_url = html_lib.escape(item["url"])

    local_path = _save_article(item, article_fetcher, is_summary)
    if local_path is not None:
        body_link = f'<a href="{html_lib.escape(local_path)}">本文だけ</a>'
    else:
        body_link = '<span class="empty">（本文を取得できませんでした）</span>'

    return (
        '<div class="article">'
        f'<div class="time">{time_label}</div>'
        f'<div class="title">{title}</div>'
        '<div class="links">'
        f'<a href="{original_url}" target="_blank" rel="noopener">元の記事</a>'
        f'{body_link}'
        '</div></div>'
    )


def _build_section(result: dict) -> str:
    site = result["site"]
    site_name = html_lib.escape(site["name"])
    parts = [f"<h2>{site_name}</h2>"]

    if result["error"] is not None:
        parts.append(f'<p class="error">（取得エラー: {html_lib.escape(result["error"])}）</p>')
        return "\n".join(parts)

    if not result["items"]:
        if result["first_page_had_items"]:
            parts.append('<p class="empty">（直近12時間以内の見出しはありませんでした）</p>')
        else:
            parts.append('<p class="empty">（見出しを抽出できませんでした。ページ構成が変わった可能性があります）</p>')
        return "\n".join(parts)

    for item in result["items"]:
        parts.append(_build_article_div(item, site["article_fetcher"], site["article_is_summary"]))
    if result["hit_page_limit"]:
        parts.append('<p class="empty">（ページの上限に達したため打ち切った可能性があります）</p>')
    return "\n".join(parts)


def build_html(results: list[dict], now: datetime) -> str:
    """縦に並べる通常版。"""
    sections = "\n".join(_build_section(r) for r in results)
    generated_at = now.strftime("%Y年%m月%d日 %H:%M")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>ニュース見出し一覧</title>
<style>{_STYLE}</style>
</head>
<body>
<h1>ニュース見出し一覧</h1>
<p class="updated">取得日時：{generated_at}　<span class="switch"><a href="report2.html">横並び版で見る</a></span></p>
{sections}
</body>
</html>
"""


def build_html_2col(results: list[dict], now: datetime) -> str:
    """NHK・時事通信を左右に並べる横並び版。"""
    columns = "\n".join(f'<div class="column">{_build_section(r)}</div>' for r in results)
    generated_at = now.strftime("%Y年%m月%d日 %H:%M")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>ニュース見出し一覧（横並び）</title>
<style>{_STYLE_2COL}</style>
</head>
<body>
<h1>ニュース見出し一覧（横並び）</h1>
<p class="updated">取得日時：{generated_at}　<span class="switch"><a href="index.html">縦並び版で見る</a></span></p>
<div class="columns">
{columns}
</div>
</body>
</html>
"""


def save_html_reports(results: list[dict], now: datetime) -> tuple[Path, Path]:
    """縦並び版（index.html）・横並び版（report2.html）の両方を組み立てて保存する。

    毎回すべての記事本文を新規取得する（キャッシュなし）。
    戻り値: (index.htmlのパス, report2.htmlのパス)
    """
    _OUTPUT_DIR.mkdir(exist_ok=True)
    _OUTPUT_PATH.write_text(build_html(results, now), encoding="utf-8")
    _OUTPUT_PATH_2COL.write_text(build_html_2col(results, now), encoding="utf-8")
    return _OUTPUT_PATH, _OUTPUT_PATH_2COL
