"""ニュース見出し自動取得ツールの実行の入り口。

サイトごとに「取得 → 解析 → 直近12時間で絞り込み → 表示」を行う。
1つのサイトで失敗しても、残りのサイトの処理は続ける。
"""

import argparse
import webbrowser
from datetime import datetime, timezone, timedelta

import config
import fetcher
import report
import timeutil

_HOURS_WITHIN = 12
_MAX_PAGES = 20  # 通常は12時間の壁で先に打ち切られるはずの安全弁


def collect_headlines(site: dict, now: datetime) -> tuple[list[dict], bool, bool]:
    """新着一覧を1ページ目から辿り、直近12時間以内の記事だけを集める。

    戻り値: (集めた記事一覧, 1ページ目で記事が1件でも読み取れたか, ページ上限に達したか)
    1ページ目の取得に失敗した場合は例外がそのまま呼び出し元に伝わる。
    """
    items = []
    seen_urls = set()
    first_page_had_items = False
    hit_page_limit = False

    page = 1
    while True:
        page_url = fetcher.build_page_url(site["url"], page)
        try:
            html = site["fetch"](page_url)
        except Exception:
            if page == 1:
                raise
            break  # 2ページ目以降の取得失敗は「ページが尽きた」とみなす

        page_items = site["parser"](html)
        if page == 1 and page_items:
            first_page_had_items = True
        if not page_items:
            break  # ページが尽きた

        stop = False
        for item in page_items:
            if item["url"] in seen_urls:
                continue
            seen_urls.add(item["url"])
            parsed_time = site["time_parser"](item["time"], now)
            if parsed_time is None:
                continue  # 時刻が解釈できない項目は対象外
            if not timeutil.is_within_hours(parsed_time, now, _HOURS_WITHIN):
                stop = True  # 新着順なので、これ以降は全て範囲外のはず
                break
            items.append(item)

        if stop or not site["paginate"]:
            break
        page += 1
        if page > _MAX_PAGES:
            hit_page_limit = True
            break

    return items, first_page_had_items, hit_page_limit


def print_headlines(site_name: str, items: list[dict], first_page_had_items: bool) -> None:
    print(f"===== {site_name} =====")
    if not items:
        if first_page_had_items:
            print("（直近12時間以内の見出しはありませんでした）")
        else:
            print("（見出しを抽出できませんでした。ページ構成が変わった可能性があります）")
        return
    for item in items:
        time_label = item["time"] or "時刻不明"
        print(f"[{time_label}] {item['title']}")
        print(f"        {item['url']}")


def main(quiet: bool = False) -> None:
    """quiet=Trueの場合、コンソール表示とブラウザの自動起動を行わない（定期自動実行向け）。"""
    now = datetime.now(timezone(timedelta(hours=9)))
    results = []  # HTML版のレポート作成用に、サイトごとの結果をためておく

    for site in config.SITES:
        try:
            items, first_page_had_items, hit_page_limit = collect_headlines(site, now)
        except Exception as e:
            if not quiet:
                print(f"===== {site['name']} =====")
                print(f"（取得エラー: {e}）")
                print()
            results.append({
                "site": site, "error": str(e),
                "items": None, "first_page_had_items": None, "hit_page_limit": False,
            })
            continue

        if not quiet:
            print_headlines(site["name"], items, first_page_had_items)
            if hit_page_limit:
                print("（ページの上限に達したため打ち切った可能性があります）")
            print()
        results.append({
            "site": site, "error": None,
            "items": items, "first_page_had_items": first_page_had_items, "hit_page_limit": hit_page_limit,
        })

    report_path, report_path_2col = report.save_html_reports(results, now)
    if not quiet:
        print(f"Webブラウザで見る用のファイルも保存しました: {report_path}")
        print(f"横並び版も保存しました: {report_path_2col}")
        webbrowser.open(report_path.as_uri())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quiet", action="store_true",
        help="コンソール表示とブラウザの自動起動を行わない（定期自動実行向け）",
    )
    args = parser.parse_args()
    main(quiet=args.quiet)
