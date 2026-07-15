"""textise.net経由で取得したHTMLから、見出し・時刻・リンクだけを抜き出す処理。

NHK・時事通信それぞれ専用の関数を用意する。どちらも失敗時は例外を投げず、
空リストを返す（呼び出し側で「抽出できませんでした」という表示に変換する）。
"""

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_NHK_BASE_URL = "https://news.web.nhk"
_NHK_TIME_PATTERN = re.compile(r"(\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2})\s*$")

_JIJI_BASE_URL = "https://www.jiji.com"
_JIJI_TIME_PATTERN = re.compile(r"\((\d{1,2}/\d{1,2}\s*\d{1,2}:\d{2})\)")


def parse_nhk(html: str) -> list[dict]:
    """NHKニュース新着一覧から見出し・時刻・リンクを抜き出す。

    textise.net変換後のHTML・NHKページを直接取得したHTMLの両方に対応するため、
    クラス名では絞り込まず、記事リンクのURLパターン（/newsweb/na/を含む）だけで判定する。
    直接取得の場合、ページ内に「新着・注目」の固定セクションが別途あり記事が重複することがあるが、
    呼び出し側（main.py）でのURL重複除去・12時間より古い記事が出た時点での打ち切りにより実害はない。
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []
    seen_urls = set()
    for a in soup.find_all("a", href=re.compile(r"/newsweb/na/")):
        url = urljoin(_NHK_BASE_URL, a["href"])
        if url in seen_urls:
            continue
        text = a.get_text(separator=" ", strip=True)
        match = _NHK_TIME_PATTERN.search(text)
        if not match:
            continue
        title = text[: match.start()].strip()
        if not title:
            continue
        seen_urls.add(url)
        items.append({
            "time": match.group(1),
            "title": title,
            "url": url,
        })
    return items


def parse_jiji(html: str) -> list[dict]:
    """時事通信ニュース新着一覧（textise.net変換後）から見出し・時刻・リンクを抜き出す。

    ページ内には「アクセスランキング」など、新着一覧とは別のセクションにも
    同じ形式のリンクが登場する。これらは時刻表示を伴わないため、時刻が
    取れなかった項目は新着一覧のものではないと判断して除外する。
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for a in soup.find_all("a", href=re.compile(r"^/jc/article\?")):
        title_tag = a.find("p")
        if title_tag is None:
            continue
        title = title_tag.get_text(strip=True)
        if not title:
            continue
        match = _JIJI_TIME_PATTERN.search(a.get_text())
        if not match:
            continue
        items.append({
            "time": match.group(1),
            "title": title,
            "url": urljoin(_JIJI_BASE_URL, a["href"]),
        })
    return items
