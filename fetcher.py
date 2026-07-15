"""textise.net経由でニュース一覧ページのHTMLを取得する処理。"""

from urllib.parse import quote

import requests

_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
}

_TEXTISE_HEADERS = {
    **_BASE_HEADERS,
    # Refererを付けないとtextise.netに403で拒否されるため必須
    "Referer": "https://www.textise.net/",
}


def build_textise_url(original_url: str) -> str:
    """textise.netの仕様（strURLパラメータを二重にURLエンコードする）に合わせてURLを組み立てる。"""
    once = quote(original_url, safe="/")
    twice = quote(once, safe="/")
    return f"https://www.textise.net/showText.aspx?strURL={twice}"


def build_page_url(base_url: str, page: int) -> str:
    """一覧ページのURLにページ番号を付ける。1ページ目はbase_urlのまま。"""
    if page <= 1:
        return base_url
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page}"


def fetch_textise_html(original_url: str, timeout: int = 15) -> str:
    """textise.net経由で変換済みのHTMLを取得する。失敗時は例外がそのまま呼び出し元に伝わる。"""
    url = build_textise_url(original_url)
    response = requests.get(url, headers=_TEXTISE_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_direct_html(url: str, timeout: int = 15) -> str:
    """textise.netを経由せず、ページのHTMLを直接取得する。失敗時は例外がそのまま呼び出し元に伝わる。"""
    response = requests.get(url, headers=_BASE_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text
