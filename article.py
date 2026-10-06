"""記事本文（またはその要約）を取得する処理。

textise.netがCloudflareのボット対策でブロックされる場合があるため、
記事ページ自体を直接取得し、そこから読める範囲のテキストを抜き出す。
"""

import re

from bs4 import BeautifulSoup

import fetcher

_NHK_DESCRIPTION_PREFIX = re.compile(r"^【NHK】")


def fetch_nhk_summary(url: str) -> str | None:
    """NHK記事ページのdescriptionメタタグから要約文を取得する。

    NHKの記事詳細ページは要約文までしか公開しておらず、本文全体は掲載されていない
    （ブラウザで実際のページを開いて確認済み）。取得できない場合はNoneを返す。
    """
    try:
        html = fetcher.fetch_direct_html(url)
    except Exception:  # noqa: BLE001 取得失敗は何であれ「本文なし」として扱い、他の記事の処理を続ける
        return None
    soup = BeautifulSoup(html, "html.parser")
    meta =soup.find("meta", attrs={"name": "description"})
    if meta is None or not meta.get("content"):
        return None
    return _NHK_DESCRIPTION_PREFIX.sub("", meta["content"].strip()).strip()


def fetch_jiji_body(url: str) -> str | None:
    """時事通信記事ページから本文全文を取得する。取得できない場合はNoneを返す。"""
    try:
        html = fetcher.fetch_direct_html(url)
    except Exception:  # noqa: BLE001 取得失敗は何であれ「本文なし」として扱い、他の記事の処理を続ける
        return None
    soup = BeautifulSoup(html, "html.parser")
    article_div = soup.find("div", class_="ArticleText")
    if article_div is None:
        return None

    paragraphs = []
    for p in article_div.find_all("p", recursive=False):
        if "ArticleTextTab" in (p.get("class") or []):
            continue  # 関連記事へのリンクなので本文ではない
        text = p.get_text(strip=True)
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs) if paragraphs else None
