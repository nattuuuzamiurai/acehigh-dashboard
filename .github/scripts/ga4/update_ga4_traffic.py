#!/usr/bin/env python3
"""
update_ga4_traffic.py

【2026-09-01】GA4アクセス数更新をGitHub Actionsに移行するための実装。
既存の cloude会社/.claude/scripts/ga4-watch-daemon.js (launchdで6時間おきに
このPC上で実行、対話的OAuth認証のトークンに依存) のロジックをPythonに移植した。
GitHub Actions側はサービスアカウント認証(ga4_auth.py)を使うため対話操作が
不要で、このPCが起動していなくても動く(2026-08-31〜09-01にローカルgitの
rebase放置でGA4更新が約33時間止まった件の再発防止)。

このPC側のdaemon(6時間おき)は当面並行稼働させる(このワークフローの
動作確認が取れるまで停止しない)。両方が同時に動いても、更新済みなら
スキップする1日1回制御があるため、二重更新やコンフリクトのリスクは低い。

処理内容(daemon.jsと同じ):
  - 対象3サイト(fukuoka-poker-navi / ai-jitsumu-navi / poker-hand-media)の
    GA4データをサイトごとのPythonスクリプトで取得
  - 1日1回だけ更新(当日すでに traffic.asOf===today かつ daily を持つならスキップ)
  - niche_sites_revenue.json の traffic フィールド(累計PV/ユーザー/セッション/
    エンゲージセッションと、daily=当日・前日のPV)を更新
  - 変化がなければファイルへの書き込みも行わない
  - 実際のgit commit/pushはこのスクリプトの外側(ワークフローのシェル手順)で行う。
    このスクリプトは「更新したら0、更新対象なしなら0」を返し、変更の有無は
    `git status --porcelain` 側で判定する(daemon.js方式を踏襲)

【2026-09-01 品質管理部指摘・修正】「今日」の判定は元のdaemon.js(ローカルMac、
JST)に合わせてAsia/Tokyoで明示的に計算する。GitHub Actions(ubuntu-latest)の
デフォルトTZはUTCで、何も指定しないとcron発火時刻(UTC 15:00 = JST 24:00頃)
付近でUTC日付とJST日付がズレ、asOf/daily.dateがJST基準の他データと食い違う
ため、date.today()/datetime.now()は使わずZoneInfo("Asia/Tokyo")を明示する。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# このスクリプトは <repo>/.github/scripts/ga4/ に置かれている前提。
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
REVENUE_FILE = os.path.join(REPO_ROOT, "niche_sites_revenue.json")

PYTHON_BIN = sys.executable

SITES = [
    {
        "id": "fukuoka-poker-navi",
        "label": "ふくおかポーカーナビ",
        "script": "check_ga4_stats.py",
        "default_since": "2026-07-14",
        "source": "GA4（measurement ID: G-L7091YHTFH）",
    },
    {
        "id": "ai-jitsumu-navi",
        "label": "AI実務ナビ",
        "script": "check_ga4_stats_ai_jitsumu.py",
        "default_since": "2026-07-17",
        "source": "GA4（measurement ID: G-QSW29CYYNP）",
    },
    {
        "id": "poker-hand-media",
        "label": "ポーカーハンドメディア",
        "script": "check_ga4_stats_poker_hand_media.py",
        "default_since": "2026-07-25",
        "source": "GA4（measurement ID: G-W6Y7FK5HSM）",
    },
]


def today_str():
    return datetime.now(JST).strftime("%Y-%m-%d")


def yesterday_str():
    return (datetime.now(JST) - timedelta(days=1)).strftime("%Y-%m-%d")


def now_str():
    return datetime.now(JST).strftime("%Y-%m-%d %H:%M")


def fetch_stats(cfg):
    """指定サイトのGA4統計を取得。失敗時はNoneを返す(他サイトへ影響させない)。"""
    try:
        out = subprocess.run(
            [PYTHON_BIN, os.path.join(SCRIPT_DIR, cfg["script"])],
            cwd=SCRIPT_DIR, capture_output=True, text=True, check=True,
        )
        stats = json.loads(out.stdout)
        if stats.get("error"):
            print(f"[{cfg['id']}] GA4取得エラー: {stats['error']}", file=sys.stderr)
            return None
        return stats
    except subprocess.CalledProcessError as e:
        print(f"[{cfg['id']}] GA4取得スクリプトの実行に失敗: {e.stderr}", file=sys.stderr)
        return None
    except Exception as e:  # noqa: BLE001
        print(f"[{cfg['id']}] GA4取得スクリプトの実行に失敗: {e}", file=sys.stderr)
        return None


def main():
    today = today_str()

    with open(REVENUE_FILE, "r", encoding="utf-8") as f:
        revenue_data = json.load(f)

    sites_by_id = {s.get("id"): s for s in revenue_data.get("sites", [])}
    commit_parts = []

    for cfg in SITES:
        site = sites_by_id.get(cfg["id"])
        if site is None:
            print(f"niche_sites_revenue.json に {cfg['id']} が見つからない(スキップ)", file=sys.stderr)
            continue

        traffic = site.get("traffic") or {}
        # 1日1回制御: 当日すでに更新済み(dailyも保持済み)ならGA4取得もせずスキップ。
        if traffic.get("asOf") == today and traffic.get("daily"):
            print(f"[{cfg['id']}] 本日({today})更新済みのためスキップ(1日1回)")
            continue

        stats = fetch_stats(cfg)
        if not stats:
            continue

        since = traffic.get("since") or cfg["default_since"]
        since_launch = stats.get("sinceLaunch", {})
        new_traffic = {
            "pageViews": since_launch.get("screenPageViews"),
            "activeUsers": since_launch.get("activeUsers"),
            "sessions": since_launch.get("sessions"),
        }
        if since_launch.get("engagedSessions") is not None:
            new_traffic["engagedSessions"] = since_launch.get("engagedSessions")
        new_traffic["since"] = since
        new_traffic["asOf"] = today
        new_traffic["source"] = cfg["source"]

        today_stats = stats.get("today")
        yesterday_stats = stats.get("yesterday")
        if today_stats and yesterday_stats:
            new_traffic["daily"] = {
                "date": today,
                "pageViews": today_stats.get("screenPageViews"),
                "activeUsers": today_stats.get("activeUsers"),
                "sessions": today_stats.get("sessions"),
                "prevDate": yesterday_str(),
                "prevPageViews": yesterday_stats.get("screenPageViews"),
            }

        old_daily = traffic.get("daily") or {}
        new_daily = new_traffic.get("daily") or {}
        unchanged = (
            traffic.get("pageViews") == new_traffic.get("pageViews")
            and traffic.get("activeUsers") == new_traffic.get("activeUsers")
            and traffic.get("sessions") == new_traffic.get("sessions")
            and traffic.get("engagedSessions") == new_traffic.get("engagedSessions")
            and traffic.get("asOf") == new_traffic.get("asOf")
            and old_daily.get("date") == new_daily.get("date")
            and old_daily.get("pageViews") == new_daily.get("pageViews")
            and old_daily.get("prevPageViews") == new_daily.get("prevPageViews")
        )
        if unchanged:
            print(f"[{cfg['id']}] 変化なし(PV={new_traffic.get('pageViews')})")
            continue

        site["traffic"] = new_traffic
        # ダッシュボードの「データ更新」表示(revenue.updatedAt)も日時付きで更新する。
        if site.get("revenue") is not None:
            site["revenue"]["updatedAt"] = now_str()
        commit_parts.append(f"{cfg['label']} PV={new_traffic.get('pageViews')}")
        print(
            f"[{cfg['id']}] 更新: PV={new_traffic.get('pageViews')} "
            f"users={new_traffic.get('activeUsers')} sessions={new_traffic.get('sessions')} "
            f"本日PV={new_daily.get('pageViews', '-')} 前日PV={new_daily.get('prevPageViews', '-')}"
        )

    if not commit_parts:
        print("更新対象なし(全サイト変化なし/スキップ)")
        return

    revenue_data["generatedAt"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    with open(REVENUE_FILE, "w", encoding="utf-8") as f:
        json.dump(revenue_data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # commitメッセージ用にGitHub Actions側へ渡す(環境ファイル経由)。
    commit_message = f"GA4アクセス数を自動更新({', '.join(commit_parts)})"
    print(f"更新しました: {commit_message}")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write("changed=true\n")
            f.write(f"commit_message={commit_message}\n")


if __name__ == "__main__":
    main()
