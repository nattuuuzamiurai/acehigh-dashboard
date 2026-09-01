#!/usr/bin/env python3
"""
GA4(Google Analytics Data API)から、ふくおかポーカーナビ
(測定ID G-L7091YHTFH)のPV・アクティブユーザー数等を取得する。

【2026-09-01】認証はサービスアカウント方式に移行(ga4_auth.py参照)。
GitHub Actions・このPCどちらからでも対話操作なしで実行できる。
従来のInstalledAppFlow(ukenthe@gmail.comでのブラウザ対話認証、
token_analytics.json)はこのPC専用のフォールバックとして残している。

読み取り専用スコープのみを使用しており、GA4の設定変更は一切行わない。
"""

import os.path
import sys
import json

from googleapiclient.discovery import build

from ga4_auth import get_credentials

TARGET_MEASUREMENT_ID = "G-L7091YHTFH"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROPERTY_CACHE_PATH = os.path.join(SCRIPT_DIR, "ga4_property_cache.json")


def find_property(admin_service, measurement_id):
    """アクセス可能な全アカウント/プロパティから、指定の測定IDに紐づくGA4プロパティを探す"""
    summaries = admin_service.accountSummaries().list(pageSize=200).execute()
    for account in summaries.get("accountSummaries", []):
        for prop_summary in account.get("propertySummaries", []):
            property_path = prop_summary["property"]  # e.g. "properties/123456789"
            streams = admin_service.properties().dataStreams().list(parent=property_path).execute()
            for stream in streams.get("dataStreams", []):
                web = stream.get("webStreamData")
                if web and web.get("measurementId") == measurement_id:
                    return property_path, prop_summary.get("displayName", "")
    return None, None


def run_report(data_service, property_path, start_date, end_date):
    # engagedSessions は「10秒以上の滞在 / 2ページ以上閲覧 / コンバージョン」のいずれかを
    # 満たしたセッション。JSを実行するクローラー(海外データセンターからの流入)はほぼ0秒で
    # 抜けるためここに乗らず、PV/セッションより実際の読者数に近い指標になる(2026-07-29追加)。
    body = {
        "dateRanges": [{"startDate": start_date, "endDate": end_date}],
        "metrics": [
            {"name": "screenPageViews"},
            {"name": "activeUsers"},
            {"name": "sessions"},
            {"name": "engagedSessions"},
        ],
    }
    resp = data_service.properties().runReport(property=property_path, body=body).execute()
    rows = resp.get("rows", [])
    if not rows:
        return {"screenPageViews": 0, "activeUsers": 0, "sessions": 0, "engagedSessions": 0}
    values = rows[0]["metricValues"]
    return {
        "screenPageViews": int(values[0]["value"]),
        "activeUsers": int(values[1]["value"]),
        "sessions": int(values[2]["value"]),
        "engagedSessions": int(values[3]["value"]),
    }


def main():
    creds = get_credentials()
    data_service = build("analyticsdata", "v1beta", credentials=creds)

    property_path, display_name = None, ""
    if os.path.exists(PROPERTY_CACHE_PATH):
        cached = json.load(open(PROPERTY_CACHE_PATH))
        if cached.get("measurementId") == TARGET_MEASUREMENT_ID:
            property_path = cached.get("propertyPath")
            display_name = cached.get("displayName", "")

    if not property_path:
        # 初回、またはキャッシュが無効な場合のみAdmin APIでプロパティを探索する
        admin_service = build("analyticsadmin", "v1beta", credentials=creds)
        property_path, display_name = find_property(admin_service, TARGET_MEASUREMENT_ID)
        if not property_path:
            print(json.dumps({"error": f"measurementId {TARGET_MEASUREMENT_ID} に対応するGA4プロパティが見つかりませんでした"}, ensure_ascii=False))
            sys.exit(1)
        with open(PROPERTY_CACHE_PATH, "w") as f:
            json.dump({
                "measurementId": TARGET_MEASUREMENT_ID,
                "propertyPath": property_path,
                "displayName": display_name,
            }, f, ensure_ascii=False)

    since_launch = run_report(data_service, property_path, "2026-07-14", "today")
    last_7d = run_report(data_service, property_path, "7daysAgo", "today")
    last_28d = run_report(data_service, property_path, "28daysAgo", "today")
    # 日間ビュー。today は取得時点までの途中経過、yesterday は確定値。
    today_stats = run_report(data_service, property_path, "today", "today")
    yesterday_stats = run_report(data_service, property_path, "yesterday", "yesterday")

    print(json.dumps({
        "propertyPath": property_path,
        "propertyDisplayName": display_name,
        "sinceLaunch": since_launch,
        "last7Days": last_7d,
        "last28Days": last_28d,
        "today": today_stats,
        "yesterday": yesterday_stats,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
