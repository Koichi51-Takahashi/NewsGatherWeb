"""年情報を含まない時刻表示（NHK・時事通信）を、実行時点を基準に実時刻へ変換する処理。"""

import datetime as dt
import re

# サイトの表示と実際の時刻とのわずかなズレ・遅延を許容する幅
_CLOCK_SKEW = dt.timedelta(hours=1)

_NHK_TIME_RE = re.compile(r"(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})")
_JIJI_TIME_RE = re.compile(r"(\d{1,2})/(\d{1,2})\s*(\d{1,2}):(\d{2})")


def parse_nhk_time(time_label: str, now: dt.datetime) -> dt.datetime | None:
    match = _NHK_TIME_RE.search(time_label)
    if not match:
        return None
    month, day, hour, minute = map(int, match.groups())
    return _resolve_year(month, day, hour, minute, now)


def parse_jiji_time(time_label: str, now: dt.datetime) -> dt.datetime | None:
    match = _JIJI_TIME_RE.search(time_label)
    if not match:
        return None
    month, day, hour, minute = map(int, match.groups())
    return _resolve_year(month, day, hour, minute, now)


def _resolve_year(month: int, day: int, hour: int, minute: int, now: dt.datetime) -> dt.datetime | None:
    """月日時分に、nowを基準に年を補う。今年だと未来になる場合は去年の日付とみなす。"""
    for year in (now.year, now.year - 1):
        try:
            candidate = now.replace(
                year=year, month=month, day=day,
                hour=hour, minute=minute, second=0, microsecond=0,
            )
        except ValueError:
            continue  # 2月29日など、その年に存在しない日付
        if candidate <= now + _CLOCK_SKEW:
            return candidate
    return None


def is_within_hours(target: dt.datetime, now: dt.datetime, hours: int) -> bool:
    """targetが、now基準で直近hours時間以内かどうかを判定する。"""
    delta = now - target
    return -_CLOCK_SKEW <= delta <= dt.timedelta(hours=hours)
