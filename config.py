"""取得対象サイトの一覧。"""

import article
import fetcher
import parsers
import timeutil

SITES = [
    {
        "name": "NHKニュース（新着）",
        "url": "https://news.web.nhk/newsweb/pl/news-nwa-latest-nationwide",
        "parser": parsers.parse_nhk,
        "time_parser": timeutil.parse_nhk_time,
        # NHKのサイトはJavaScriptで画面を組み立てる作りのため、textise.net経由では
        # ?page=2以降が1ページ目と同じ内容しか返らない。直接取得なら正しくページが進む
        "fetch": fetcher.fetch_direct_html,
        "paginate": True,
        # NHKの記事詳細ページは要約文までしか公開していない（全文は無い）
        "article_fetcher": article.fetch_nhk_summary,
        "article_is_summary": True,
    },
    {
        "name": "時事通信（新着）",
        "url": "https://www.jiji.com/sp/list?g=news",
        "parser": parsers.parse_jiji,
        "time_parser": timeutil.parse_jiji_time,
        # 1ページで約2.5日分をカバーできており12時間分には十分。
        # ページ送りのURLパターンも実機確認で見つからなかったため無効のまま
        "fetch": fetcher.fetch_textise_html,
        "paginate": False,
        "article_fetcher": article.fetch_jiji_body,
        "article_is_summary": False,
    },
]
