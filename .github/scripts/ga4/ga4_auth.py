"""
GA4(Google Analytics Data/Admin API)向けの認証ヘルパー(GitHub Actions用)。

【2026-09-01】GA4アクセス数更新をGitHub Actionsに移行するための実装。
これまでの取得スクリプトはブラウザでの対話的OAuth認証(InstalledAppFlow)を
使っており、非対話環境のGitHub Actionsでは動かせなかった(この移行の背景:
2026-08-31〜09-01、ローカルgitのrebase放置で約33時間更新が止まった件の再発防止)。

このディレクトリのスクリプトはサービスアカウント認証のみに対応する
(対話フローへのフォールバックは持たない — GitHub Actions上では常に
Secretsから鍵が渡ってくる前提のため)。ローカルPC専用のInstalledAppFlow
フォールバックを持つ版は cloude会社/.claude/scripts/gmail-check/ga4_auth.py 側にある。

鍵の受け取り方:
  環境変数 GA4_SERVICE_ACCOUNT_KEY にサービスアカウント鍵のJSON文字列を
  そのまま入れる(GitHub Secretsから注入する想定)。

読み取り専用スコープ(analytics.readonly)のみを使用する。GA4の設定変更は
一切行わない。またサービスアカウント自身をGA4プロパティの閲覧者として
追加する作業は、Google Analytics Admin UIでの手動操作が必要(範囲外)。
"""

import json
import os
import sys

from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def get_credentials():
    env_key = os.environ.get("GA4_SERVICE_ACCOUNT_KEY")
    if not env_key:
        print(json.dumps({
            "error": "環境変数 GA4_SERVICE_ACCOUNT_KEY が設定されていません"
                     "(GitHub Secretsからの注入を確認してください)",
        }, ensure_ascii=False))
        sys.exit(1)
    info = json.loads(env_key)
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
